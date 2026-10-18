import { setGenreText, displayGenre, populateGenreOptions } from '/genre-ui.js';
import { findGenre } from '/genre-names.js';
import { setText, setAttr } from '/i18n.js';
import { GenreCluster } from '/genre-cluster.js';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const mode = document.body.dataset.mode;
const title = mode === 'guessr' ? 'Genreguessr' : 'Genrerace';
const state = {
  room: null, credentials: null, requestedRoom: new URL(location.href).searchParams.get('room'),
  busy: false, ready: false, page: null, selection: null, sceneKey: null,
  pollTimer: null, pollFailures: 0, epoch: 0, stopped: false, preview: null, editing: false, editingRecovery: false, polling: false,
};
let genres = new Map();
let scenes = [];
let choiceScene = null;
let playersKey = null;
let audioVersion = 0;
let audioRole = null;
let audioGenre = null;
const audio = document.createElement('audio');
audio.preload = 'none';
audio.hidden = true;
document.body.append(audio);

// A room URL is public. Only this tab's storage contains its player credential.
const storage = {
  get(key) { try { return sessionStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { sessionStorage.setItem(key, value); } catch { /* This visit still works. */ } },
  remove(key) { try { sessionStorage.removeItem(key); } catch { /* Nothing to remove. */ } },
};
const credentialKey = (id) => `genre-multiplayer:${id}`;
const roomPath = () => `/api/rooms/${encodeURIComponent(state.room?.id || state.requestedRoom)}`;
const self = () => state.room?.players.find((player) => player.id === (state.room.self_id || state.credentials?.player_id));
const activePlayers = () => state.room?.players.filter((player) => !player.left) || [];
const isHost = () => state.room?.host_id === self()?.id;
const genreId = (genre) => genre?.id;
const sameId = (left, right) => String(left) === String(right);

async function request(path, payload, token = state.credentials?.token) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const headers = { ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(payload !== undefined ? { 'Content-Type': 'application/json' } : {}) };
    const response = await fetch(path, { method: payload === undefined ? 'GET' : 'POST', headers,
      ...(payload !== undefined ? { body: JSON.stringify(payload) } : {}),
      cache: 'no-store', signal: controller.signal });
    const data = await response.json();
    if (!response.ok) throw Object.assign(new Error(data.error || 'The request could not be completed.'), { data, status: response.status });
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The server took too long to respond. Please retry.');
    throw error;
  } finally { clearTimeout(timeout); }
}

function message(text = '', selector) {
  const target = $(selector || (state.page === 'setup' ? '#setup-message' : state.page === 'join' ? '#join-message' : '#game-message'));
  setText(target, text);
  target.hidden = !text;
}

function connection(text = '', terminal = false) {
  $('#connection-banner').hidden = !text;
  setText($('#connection-message'), text);
  $('#fresh-room').hidden = !terminal;
  $('#retry-connection').hidden = terminal;
}

function showPage(page) {
  if (state.page === page) return;
  stopAudio();
  state.page = page;
  $$('.page').forEach((section) => { section.hidden = section.id !== page; });
  $('#room-shell').hidden = page === 'setup' || page === 'join';
  document.body.classList.toggle('playing', ['cluster', 'genre', 'race'].includes(page));
  document.body.classList.toggle('in-room', !$('#room-shell').hidden);
  setText(document.querySelector('title'), `Multiplayer ${title} — Cartography & BGMs`);
  window.scrollTo({ top: 0, behavior: 'instant' });
  $(`#${page} h1`)?.focus({ preventScroll: true });
}

function updateParameters() {
  const metric = $('input[name=metric]:checked').value;
  $$('.metric-parameter').forEach((row) => {
    row.hidden = !row.dataset.for.split(' ').includes(metric);
    row.querySelectorAll('input').forEach((input) => { input.disabled = row.hidden; });
  });
  $('#size-value').value = $('#cluster-size').value;
  const weight = Number($('#map-weight').value);
  $('#weight-value').value = `${weight} / ${100 - weight}`;
  if (mode === 'guessr') {
    $('#count-value').value = $('#cluster-count').value;
    $('#separation').max = metric === 'kernel' ? '2' : '10';
  }
}

function settings() {
  const metric = $('input[name=metric]:checked').value;
  if (mode === 'guessr') return {
    metric, count: Number($('#cluster-count').value),
    ...(metric !== 'graph' ? { cluster_size: Number($('#cluster-size').value) } : {}),
    alpha: Number($('#map-weight').value) / 100,
    separation: Number($(metric === 'graph' ? '#graph-separation' : '#separation').value),
    opposition: Number($('#opposition-weight').value), regularization: Number($('#regularization').value),
  };
  if (metric === 'graph') return { metric, radius: 1 };
  return { metric, cluster_size: Number($('#cluster-size').value),
    ...(metric === 'xyrgb' ? { alpha: Number($('#map-weight').value) / 100 } : {
      opposition: Number($('#opposition-weight').value), regularization: Number($('#regularization').value),
    }) };
}

function settingsSummary(room) {
  const values = room.settings || {};
  const parts = [{ xyrgb: 'XYRGB', graph: 'Graph distance', kernel: 'Signed kernel' }[values.metric] || values.metric];
  if (room.mode === 'guessr') parts.push(`${room.total_rounds || 5} rounds`, `${values.count} clusters`);
  if (values.cluster_size) parts.push(`${values.cluster_size} genres per cluster`);
  if (values.metric === 'xyrgb') parts.push(`${Math.round(values.alpha * 100)} / ${Math.round((1 - values.alpha) * 100)} position / color`);
  if (values.metric === 'kernel') parts.push(`λ ${values.opposition}`, `η ${values.regularization}`);
  if (room.mode === 'guessr') parts.push(`${values.metric === 'graph' ? 'Neighborhood separation' : 'Center separation'} ${values.separation}`);
  else if (values.metric === 'graph') parts.push('Neighborhood radius 1');
  if (room.race?.start && room.race?.goal) parts.push(`${room.race.start.name} → ${room.race.goal.name}`);
  return parts.filter(Boolean).join(' · ');
}

function setBusy(busy) {
  state.busy = busy;
  $('#room-form').setAttribute('aria-busy', String(busy));
  $$('#room-form fieldset').forEach((fieldset) => { fieldset.disabled = busy; });
  $('#player-name').disabled = busy || state.editing;
  if ($('#rounds')) $('#rounds').disabled = busy || state.editingRecovery;
  $('#cancel-edit').disabled = busy;
  $('#cancel-edit').hidden = !state.editing;
  $('#player-name').closest('.name-field').hidden = state.editing;
  $('#join-name').disabled = busy;
  $('#create-room').disabled = busy || !state.ready;
  setText($('#create-room'), busy && state.page === 'setup' ? 'Preparing…' : state.editingRecovery ? 'Update & retry round →' : state.editing ? 'Save settings →' : 'Create room →');
  $('#join-room').disabled = busy || !state.preview || state.preview.stage !== 'lobby';
  setText($('#join-room'), busy && state.page === 'join' ? 'Joining…' : 'Join room →');
  $$('.randomize-genre').forEach((button) => { button.disabled = busy || !state.ready; });
  updateControls();
}

function canChoose(stage) {
  const player = self();
  return state.room?.stage === stage && !state.busy && !state.stopped && player && !player.left &&
    (stage === 'race' || (!player.submitted && (stage !== 'genre' || player.eligible)));
}

function updateControls() {
  const room = state.room;
  const player = self();
  if (!room || !player) return;
  $('#leave-room').disabled = state.busy;
  $('#edit-settings').hidden = !isHost();
  $('#edit-settings').disabled = state.busy || state.stopped;
  $('#recover-settings').hidden = !(isHost() && room.mode === 'guessr' && room.stage === 'round_result' && room.error);
  $('#recover-settings').disabled = state.busy || state.stopped;
  $('#start-game').hidden = !isHost();
  $('#start-game').disabled = state.busy || state.stopped || activePlayers().length < 2;
  setText($('#start-game'), state.busy && room.stage === 'lobby' ? 'Preparing…' : mode === 'race' ? 'Start race →' : 'Start game →');
  $('#submit-cluster').disabled = !canChoose('cluster') || state.selection === null;
  $('#submit-genre').disabled = !canChoose('genre') || state.selection === null;
  $('#submit-move').disabled = !canChoose('race') || !state.selection || sameId(genreId(state.selection), genreId(room.race?.current));
  const retry = Boolean(isHost() && room.error?.retryable && activePlayers().every((item) => item.ready));
  $('#ready-next').disabled = state.busy || state.stopped || (player.ready && !retry);
  setText($('#ready-next'), retry ? 'Retry next round →' : player.ready ? 'Ready — waiting…' : room.round_number >= room.total_rounds ? 'Finish game →' : 'Next round →');
  $$('.remove-player').forEach((button) => { button.disabled = state.busy || state.stopped; });
  $$('.cluster-card').forEach((card) => {
    const disabled = !canChoose('cluster');
    card.setAttribute('aria-disabled', String(disabled));
    card.tabIndex = disabled ? -1 : 0;
  });
  choiceScene?.items.forEach(({ label }) => { label.disabled = !canChoose(room.stage); });
  $$('.play-link').forEach((button) => {
    button.disabled = state.busy || state.stopped || !room.game?.audio || room.game.audio_available === false;
  });
}

function disposeScenes() {
  scenes.forEach((scene) => scene.destroy());
  scenes = [];
  choiceScene = null;
}

function node(tag, text, className, localize = true) {
  const element = document.createElement(tag);
  if (text !== undefined) {
    if (localize) setText(element, text);
    else element.textContent = text;
  }
  if (className) element.className = className;
  return element;
}

function playerName(player) {
  const isSelf = player.id === self()?.id;
  return (language) => `${player.name}${isSelf ? (language === 'en' ? ' (you)' : '（你）') : ''}${player.left ? (language === 'en' ? ' · left' : ' · 已离开') : ''}`;
}

function renderPlayers() {
  const room = state.room;
  const players = room.players;
  const key = JSON.stringify([room.id, room.stage, room.host_id, room.self_id, room.winner_ids,
    players.map(({ id, name, score, submitted, eligible, ready, left }) => [id, name, score, submitted, eligible, ready, left])]);
  if (key === playersKey) return;
  playersKey = key;
  setText($('#player-count'), `${activePlayers().length} ${activePlayers().length === 1 ? 'player' : 'players'}`);
  $('#player-list').replaceChildren(...players.map((player) => {
    const item = node('li', undefined, player.left ? 'player-left' : '');
    const name = node('span', playerName(player), 'player-name');
    if (player.id === room.host_id) name.append(node('span', 'Host', 'host-label'));
    const status = node('span', '', 'player-status');
    if (player.left) setText(status, 'Left');
    else if (room.stage === 'lobby') setText(status, 'Joined');
    else if (room.stage === 'cluster') setText(status, player.submitted ? 'Selected' : 'Choosing…');
    else if (room.stage === 'genre') setText(status, !player.eligible ? '0 this round' : player.submitted ? 'Selected' : 'Choosing…');
    else if (room.stage === 'round_result') setText(status, player.ready ? 'Ready' : 'Reviewing…');
    else if (room.stage === 'race') setText(status, 'Racing');
    else setText(status, room.winner_ids?.includes(player.id) ? 'Winner' : 'Finished');
    item.append(name, status);
    if (mode === 'guessr') item.append(node('span', `${player.score || 0} pts`, 'player-score'));
    if (isHost() && player.id !== self()?.id && !player.left && room.stage !== 'finished') {
      const remove = node('button', 'Remove', 'text-button remove-player');
      remove.type = 'button';
      setAttr(remove, 'aria-label', `Remove ${player.name} from the room`);
      setAttr(remove, 'title', 'Remove a player who has left or disconnected');
      remove.addEventListener('click', () => act('remove', { player_id: player.id }));
      item.append(remove);
    }
    return item;
  }));
}

function renderCluster() {
  $('#cluster-grid').replaceChildren();
  (state.room.game?.clusters || []).forEach((group, index) => {
    const card = node('div', undefined, 'cluster-card');
    card.tabIndex = 0;
    card.setAttribute('role', 'button');
    card.setAttribute('aria-pressed', 'false');
    setAttr(card, 'aria-label', `Cluster ${index + 1}: ${group.genres.map((genre) => genre.name).join(', ')}`);
    const viewport = node('div', undefined, 'cluster-viewport');
    card.append(viewport);
    $('#cluster-grid').append(card);
    scenes.push(new GenreCluster(viewport, group.genres));
    const choose = () => {
      if (!canChoose('cluster')) return;
      state.selection = group.id;
      $$('.cluster-card').forEach((other) => {
        other.classList.toggle('is-selected', other === card);
        other.setAttribute('aria-pressed', String(other === card));
      });
      setText($('#game-announcement'), `Cluster ${index + 1} selected. Press Select to submit.`);
      message();
      updateControls();
    };
    card.addEventListener('click', choose);
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(); }
    });
  });
}

function renderGenreCluster() {
  const room = state.room;
  const cluster = room.stage === 'race' ? room.race?.cluster : room.game?.cluster;
  if (!cluster) return;
  const viewport = $(room.stage === 'race' ? '#race-viewport' : '#genre-viewport');
  choiceScene = new GenreCluster(viewport, cluster.genres, {
    selectable: true, large: true,
    onSelect: (name, genre) => {
      if (!canChoose(state.room.stage)) return;
      state.selection = genre;
      choiceScene.select(name);
      setText($('#game-announcement'), `${name} selected. Press Select to ${room.stage === 'race' ? 'move' : 'submit'}.`);
      message();
      updateControls();
      const source = room.stage === 'race' ? `/api/genres/${encodeURIComponent(genre.id)}/audio` :
        `${roomPath()}/audio/${room.round_number}/candidate/${encodeURIComponent(genre.id)}`;
      playAudio(source, 'candidate', genre);
    },
  });
  scenes.push(choiceScene);
  choiceScene.items.forEach(({ genre, label }) => {
    setAttr(label, 'title', `Listen to ${genre.name}`);
    if (room.stage === 'race' && sameId(genre.id, room.race.current.id)) {
      label.classList.add('race-current');
      label.setAttribute('aria-current', 'location');
      setAttr(label, 'aria-label', `${genre.name}, current genre`);
    }
  });
}

function renderRoute(route, container) {
  container.replaceChildren(...(route || []).map((genre, index) => {
    const item = node('li');
    if (index > 0) {
      const arrow = node('span', '→', 'trace-separator');
      arrow.setAttribute('aria-hidden', 'true');
      item.append(arrow);
    }
    const label = node('span', undefined, 'trace-genre');
    setGenreText(label, genre.name);
    label.style.color = genre.color || '';
    item.append(label);
    return item;
  }));
}

function renderScoreboard(container, result, final = false) {
  const table = node('table', undefined, 'score-table');
  const caption = node('caption', final ? 'Final scores' : 'Round scores', 'sr-only');
  const head = node('thead');
  const header = node('tr');
  (final ? ['Player', 'Total'] : ['Player', 'Guess', 'Round', 'Total']).forEach((text) => {
    const cell = node('th', text);
    cell.scope = 'col';
    header.append(cell);
  });
  head.append(header);
  const body = node('tbody');
  const players = final ? [...state.room.players].sort((a, b) => b.score - a.score) : result?.players || [];
  players.forEach((player) => {
    const row = node('tr');
    const name = node('th', playerName(player));
    name.scope = 'row';
    row.append(name);
    if (!final) {
      const guess = player.cluster_correct === false ? 'Wrong cluster' : player.guess?.name || (typeof player.guess === 'string' ? player.guess : '—');
      const guessCell = node('td');
      if (player.cluster_correct === false) setText(guessCell, guess);
      else setGenreText(guessCell, guess);
      row.append(guessCell, node('td', `+${player.round_score || 0}`));
    }
    row.append(node('td', String(player.score || 0)));
    body.append(row);
  });
  table.append(caption, head, body);
  container.replaceChildren(table);
}

function waitingFor(players, prefix = 'Waiting for') {
  return players.length ? `${prefix} ${players.map((player) => player.name).join(', ')}.` : 'Everyone has selected. Moving on…';
}

function applySnapshot(value) {
  const room = value.room || value;
  if (room.mode !== mode) {
    // Both modes share tab credentials; correct an invite opened on the wrong page.
    location.replace(`/multiplayer-genre${room.mode}?room=${encodeURIComponent(room.id)}`);
    return;
  }
  state.room = room;
  state.requestedRoom = room.id;
  const player = self();
  if (!player || player.left) {
    state.stopped = true;
    stopAudio();
    clearTimeout(state.pollTimer);
    connection(player?.left ? 'You have left this room or were removed by the host.' : 'Your player session is no longer available.', true);
    updateControls();
    return;
  }
  const sceneKey = `${room.stage}:${room.round_number || 0}:${room.race?.revision || 0}:${player.eligible}`;
  const changed = state.sceneKey !== sceneKey;
  if (changed) {
    stopAudio();
    disposeScenes();
    state.selection = null;
    state.sceneKey = sceneKey;
    message('', '#game-message');
  }
  showPage(room.stage === 'round_result' ? 'round-result' : room.stage);
  setText($('#room-label'), `${title} · ${room.id}`);
  renderPlayers();
  const progress = `Round ${room.round_number} of ${room.total_rounds}`;
  if (room.stage === 'lobby') {
    $('#invite-link').value = `${location.origin}/multiplayer-genre${mode}?room=${encodeURIComponent(room.id)}`;
    setText($('#lobby-settings'), settingsSummary(room));
    setText($('#lobby-waiting'), isHost() ? activePlayers().length < 2 ? 'Waiting for a friend. At least 2 players are needed.' : 'Everyone is here? Start when you’re ready.' : 'Waiting for the host to start.');
    if (['localhost', '127.0.0.1', '[::1]'].includes(location.hostname)) {
      setText($('#invite-note'), 'For friends on other devices, open this site through its shared network address before copying the link.');
    }
  } else if (room.stage === 'cluster') {
    setText($('#cluster-progress'), `${progress} · Stage 1 of 2`);
    if (changed) renderCluster();
    setText($('#cluster-waiting'), player.submitted ? `Your choice is in. ${waitingFor(activePlayers().filter((item) => !item.submitted))}` : 'Listen, choose a cluster, then press Select. Everyone submits before the next stage.');
  } else if (room.stage === 'genre') {
    setText($('#genre-progress'), `${progress} · Stage 2 of 2`);
    $('#genre-playing').hidden = !player.eligible;
    if (changed && player.eligible) renderGenreCluster();
    const pending = activePlayers().filter((item) => item.eligible && !item.submitted);
    setText($('#genre-waiting'), !player.eligible ? `Your cluster was incorrect: 0 points this round. ${waitingFor(pending)}` :
      player.submitted ? `Your choice is in. ${waitingFor(pending)}` : 'Choose a genre to listen, then press Select. Closer guesses earn more points.');
  } else if (room.stage === 'round_result') {
    setText($('#result-progress'), progress);
    const target = room.result?.target;
    setGenreText($('#target-genre'), target?.name || '—');
    $('#target-genre').style.color = target?.color || '';
    renderScoreboard($('#round-scoreboard'), room.result);
    const pending = activePlayers().filter((item) => !item.ready);
    setText($('#result-waiting'), pending.length ? waitingFor(pending, 'Ready when everyone is. Waiting for') : room.error?.retryable ? 'The next round could not load. The host can retry.' : 'Everyone is ready. Preparing the next stage…');
  } else if (room.stage === 'race') {
    setGenreText($('#race-goal-name'), room.race.goal.name);
    $('#race-goal-name').style.color = room.race.goal.color || '';
    setText($('#trace-count'), `${room.race.moves} ${room.race.moves === 1 ? 'move' : 'moves'}`);
    if (changed) {
      renderGenreCluster();
      renderRoute(room.race.route, $('#race-trace'));
    }
    setText($('#race-note'), room.race.goal_reachable === false ? 'The goal is unreachable from this genre.' : `At ${room.race.current.name}. Choose a genre, then Select to move.`);
  } else if (room.stage === 'finished') {
    const winners = room.players.filter((item) => room.winner_ids?.includes(item.id));
    setText($('#winner-message'), winners.length ? `${winners.map((item) => item.name).join(' & ')} ${winners.length > 1 ? 'win' : 'wins'}${mode === 'race' ? ' the race' : ''}!` : 'The game has ended.');
    $('#final-scoreboard').hidden = mode === 'race';
    $('#all-routes').hidden = mode !== 'race';
    if (mode === 'guessr') renderScoreboard($('#final-scoreboard'), room.result, true);
    else $('#all-routes').replaceChildren(...(room.routes || []).map((playerRoute) => {
      const section = node('section', undefined, 'finished-route');
      const heading = node('div', undefined, 'trace-heading');
      heading.append(node('h2', (language) => `${playerRoute.name}${room.winner_ids?.includes(playerRoute.id) ? (language === 'en' ? ' · Winner' : ' · 获胜') : ''}`),
        node('span', `${playerRoute.moves} ${playerRoute.moves === 1 ? 'move' : 'moves'}`));
      const route = node('ol', undefined, 'route-list');
      setAttr(route, 'aria-label', `${playerRoute.name}’s route`);
      renderRoute(playerRoute.route, route);
      section.append(heading, route);
      return section;
    }));
    clearTimeout(state.pollTimer);
  }
  if (room.error?.error) message(room.error.error);
  else if (changed && ['cluster', 'genre'].includes(room.stage) && room.game?.audio_available === false && (room.stage === 'cluster' || player.eligible)) message('This sample is unavailable. You can still select an answer.');
  if (changed) setText($('#game-announcement'), `${room.stage === 'lobby' ? 'Lobby.' : room.stage === 'finished' ? 'Game finished.' : mode === 'guessr' ? `${progress}.` : 'Race started.'} ${$(`#${state.page} h1`)?.textContent || ''}`);
  updateControls();
}

function saveCredentials(result) {
  state.credentials = { player_id: result.player_id, token: result.token };
  storage.set(credentialKey(result.room.id), JSON.stringify(state.credentials));
  state.requestedRoom = result.room.id;
  history.replaceState(null, '', `/multiplayer-genre${mode}?room=${encodeURIComponent(result.room.id)}`);
  state.stopped = false;
  state.pollFailures = 0;
  connection();
  applySnapshot(result.room);
  schedulePoll();
}

function schedulePoll(delay = 800) {
  clearTimeout(state.pollTimer);
  if (!state.credentials || state.stopped || state.room?.stage === 'finished') return;
  state.pollTimer = setTimeout(poll, delay);
}

function terminalError(error) {
  const code = error.data?.code;
  if (!['room_not_found', 'invalid_token', 'player_left'].includes(code)) return false;
  state.stopped = true;
  clearTimeout(state.pollTimer);
  stopAudio();
  if (code === 'invalid_token') storage.remove(credentialKey(state.requestedRoom));
  connection(code === 'room_not_found' ? 'This room has expired or no longer exists. Create a new room to play again.' :
    code === 'player_left' ? 'You have left this room or were removed by the host.' : 'This player session is no longer valid. Open the invitation again to join if the lobby is still open.', true);
  updateControls();
  return true;
}

async function poll() {
  if (state.busy || state.editing || state.polling || state.stopped || !state.credentials) { schedulePoll(); return; }
  state.polling = true;
  const epoch = state.epoch;
  try {
    const room = await request(roomPath());
    if (epoch !== state.epoch) return;
    state.pollFailures = 0;
    connection();
    applySnapshot(room);
  } catch (error) {
    if (epoch !== state.epoch) return;
    if (terminalError(error)) return;
    state.pollFailures++;
    connection('Connection interrupted. Reconnecting… Your place in the room is saved.');
  } finally {
    state.polling = false;
    if (epoch === state.epoch) schedulePoll(Math.min(8000, 800 * 2 ** state.pollFailures));
  }
}

async function act(action, payload = {}) {
  if (state.busy || state.stopped || !state.credentials) return;
  clearTimeout(state.pollTimer);
  state.epoch++;
  message();
  stopAudio();
  setBusy(true);
  try {
    const room = await request(`${roomPath()}/${action}`, payload);
    state.pollFailures = 0;
    connection();
    applySnapshot(room);
  } catch (error) {
    if (!terminalError(error)) {
      // An interrupted response may still have saved the selection. Reconcile
      // before allowing another click, so the screen never invents a result.
      try { applySnapshot(await request(roomPath())); } catch (syncError) {
        if (!terminalError(syncError)) connection('Connection interrupted. Reconnecting… Your place in the room is saved.');
      }
      message(error.message || 'The action could not be saved. Please retry.');
    }
  } finally { setBusy(false); schedulePoll(); }
}

function audioIndicator(status = '') {
  $$('.play-link').forEach((button) => {
    const active = audioRole === 'clue';
    setText(button.querySelector('span'), active && status === 'loading' ? '…' : active && status === 'playing' ? 'Ⅱ' : '▷');
    setAttr(button, 'aria-label', `${active && status === 'playing' ? 'Pause' : 'Play'} ${state.room?.stage === 'genre' ? 'second' : 'first'} sample`);
  });
  choiceScene?.items.forEach(({ genre, label }) => {
    const active = audioRole === 'candidate' && sameId(genre.id, audioGenre?.id);
    label.classList.toggle('gc-loading', active && status === 'loading');
    label.classList.toggle('gc-listening', active && status === 'playing');
    label.setAttribute('aria-busy', String(active && status === 'loading'));
  });
}

function stopAudio() {
  audioVersion++;
  audioRole = null;
  audioGenre = null;
  audio.pause();
  audio.removeAttribute('src');
  audio.load();
  audioIndicator();
}

async function playAudio(source, role, genre = null) {
  stopAudio();
  if (!source || state.stopped) return;
  audioRole = role;
  audioGenre = genre;
  const version = audioVersion;
  const url = new URL(source, location.origin);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/rooms/')) url.searchParams.set('token', state.credentials.token);
  audio.src = url.href;
  audioIndicator('loading');
  try { await audio.play(); } catch {
    if (version !== audioVersion) return;
    audioIndicator();
    message(`Sample unavailable${genre ? ` for ${genre.name}` : ''}. Try playing it again.`);
  }
}

audio.addEventListener('playing', () => {
  if (!audioRole || !['cluster', 'genre', 'race'].includes(state.room?.stage) || state.stopped) { audio.pause(); return; }
  audioIndicator('playing');
});
audio.addEventListener('pause', () => audioIndicator());
audio.addEventListener('ended', () => audioIndicator());
audio.addEventListener('error', () => {
  if (!audioRole || !audio.error || !audio.getAttribute('src')) return;
  audioIndicator();
  message('Sample unavailable. Try playing it again.');
});
$$('.play-link').forEach((button) => button.addEventListener('click', () => {
  if (audioRole === 'clue' && !audio.paused) { audio.pause(); return; }
  message();
  playAudio(state.room?.game?.audio, 'clue');
}));

$('#room-form').addEventListener('input', updateParameters);
$('#room-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (state.busy || !state.ready) return;
  const name = $('#player-name').value.trim();
  if (!name && !state.editing) { message('Enter your name to create a room.'); $('#player-name').focus(); return; }
  const payload = { mode, name, settings: settings() };
  if (mode === 'guessr') {
    if (!state.editingRecovery) payload.rounds = Number($('#rounds').value);
  } else {
    const start = findGenre(genres, $('#start-genre').value);
    const goal = findGenre(genres, $('#goal-genre').value);
    if (!start || !goal) {
      message('Choose a start and goal from the genre suggestions.');
      $(!start ? '#start-genre' : '#goal-genre').focus();
      return;
    }
    Object.assign(payload, { start_id: start.id, goal_id: goal.id });
  }
  storage.set('genre-multiplayer:name', name);
  message();
  setBusy(true);
  try {
    if (state.editing) {
      const room = await request(`${roomPath()}/configure`, payload);
      state.editing = false;
      state.editingRecovery = false;
      applySnapshot(room);
      schedulePoll();
    } else saveCredentials(await request('/api/rooms', payload, null));
  } catch (error) {
    if (state.editing) {
      // A configure request can save settings before round preparation fails.
      // Keep the editor usable, but reconcile for Cancel or a lost success response.
      try {
        const room = await request(roomPath());
        state.room = room;
        if (!['lobby', 'round_result'].includes(room.stage)) {
          state.editing = false;
          state.editingRecovery = false;
          applySnapshot(room);
          schedulePoll();
        }
      } catch (syncError) { terminalError(syncError); }
    }
    message(error.message || 'The room could not be saved. Please retry.');
  }
  finally { setBusy(false); }
});

$$('.randomize-genre').forEach((button) => button.addEventListener('click', () => {
  if (!state.ready || state.busy) return;
  const choices = [...genres.values()];
  const genre = choices[Math.floor(Math.random() * choices.length)];
  document.getElementById(button.dataset.input).value = displayGenre(genre.name);
  setText($('#randomization-status'), `${button.dataset.input === 'start-genre' ? 'Start' : 'Goal'}: ${genre.name}.`);
  message();
}));

$('#join-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (state.busy || state.preview?.stage !== 'lobby') return;
  const name = $('#join-name').value.trim();
  if (!name) { message('Enter your name to join.'); $('#join-name').focus(); return; }
  storage.set('genre-multiplayer:name', name);
  message();
  setBusy(true);
  try { saveCredentials(await request(`${roomPath()}/join`, { name }, null)); }
  catch (error) { message(error.message || 'The room could not be joined. Please retry.'); }
  finally { setBusy(false); }
});

async function openSettings(recovery = false) {
  const canRecover = mode === 'guessr' && state.room?.stage === 'round_result' && state.room.error;
  if (!isHost() || state.busy || (recovery ? !canRecover : state.room.stage !== 'lobby')) return;
  state.editing = true;
  state.editingRecovery = recovery;
  state.epoch++;
  clearTimeout(state.pollTimer);
  const values = state.room.settings;
  const metric = $(`input[name=metric][value=${values.metric}]`);
  if (metric) metric.checked = true;
  const fields = { '#cluster-size': values.cluster_size, '#map-weight': Math.round((values.alpha ?? 0.8) * 100),
    '#opposition-weight': values.opposition, '#regularization': values.regularization,
    '#cluster-count': values.count, '#rounds': state.room.total_rounds,
    '#separation': values.metric === 'graph' ? undefined : values.separation,
    '#graph-separation': values.metric === 'graph' ? values.separation : undefined,
    '#start-genre': state.room.race?.start?.name, '#goal-genre': state.room.race?.goal?.name };
  for (const [selector, value] of Object.entries(fields)) if ($(selector) && value !== undefined) $(selector).value = value;
  $('#player-name').value = self().name;
  updateParameters();
  showPage('setup');
  message(recovery ? 'Adjust the arrangement to retry the next round. Scores and the number of rounds stay the same.' : 'Update the room settings. Your invited players stay in the lobby.');
  setBusy(false);
  if (!state.ready) await loadCatalog();
}
$('#edit-settings').addEventListener('click', () => openSettings());
$('#recover-settings').addEventListener('click', () => openSettings(true));
$('#cancel-edit').addEventListener('click', () => {
  state.editing = false;
  state.editingRecovery = false;
  applySnapshot(state.room);
  setBusy(false);
  schedulePoll(0);
});
$('#start-game').addEventListener('click', () => act('start'));
$('#submit-cluster').addEventListener('click', () => {
  if (canChoose('cluster') && state.selection !== null) act('cluster', { cluster_id: state.selection, round_number: state.room.round_number });
});
$('#submit-genre').addEventListener('click', () => {
  if (canChoose('genre') && state.selection !== null) act('genre', { genre_id: state.selection.id, round_number: state.room.round_number });
});
$('#submit-move').addEventListener('click', () => {
  if (canChoose('race') && state.selection && !sameId(state.selection.id, state.room.race.current.id)) {
    act('move', { genre_id: state.selection.id, revision: state.room.race.revision });
  }
});
$('#ready-next').addEventListener('click', () => act('ready', { round_number: state.room.round_number }));
$('#leave-room').addEventListener('click', async () => {
  if (state.busy || !state.credentials) return;
  clearTimeout(state.pollTimer);
  state.epoch++;
  stopAudio();
  setBusy(true);
  try {
    await request(`${roomPath()}/leave`, {});
    storage.remove(credentialKey(state.room.id));
    location.assign(`/multiplayer-genre${mode}`);
  } catch (error) {
    if (terminalError(error)) {
      storage.remove(credentialKey(state.room.id));
      location.assign(`/multiplayer-genre${mode}`);
    } else message('Could not leave the room yet. Please retry when connected.');
  } finally { setBusy(false); schedulePoll(); }
});
$('#copy-link').addEventListener('click', async () => {
  const input = $('#invite-link');
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(input.value);
    setText($('#invite-note'), 'Link copied. Send it to your friends.');
  } catch {
    input.focus();
    input.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch { /* Manual copy remains available. */ }
    setText($('#invite-note'), copied ? 'Link copied. Send it to your friends.' : 'Select and copy this link, then send it to your friends.');
  }
});
$('#retry-connection').addEventListener('click', () => {
  state.pollFailures = 0;
  if (state.editing && !state.ready) loadCatalog();
  else if (state.credentials) { clearTimeout(state.pollTimer); poll(); }
  else if (state.requestedRoom) loadInvite();
  else loadCatalog();
});
window.addEventListener('online', () => { if (state.credentials && !state.stopped) schedulePoll(0); });
window.addEventListener('offline', () => { if (state.credentials && !state.stopped) connection('You’re offline. Reconnecting when your connection returns…'); });
window.addEventListener('pagehide', () => { clearTimeout(state.pollTimer); state.epoch++; stopAudio(); });
window.addEventListener('pageshow', (event) => { if (event.persisted) schedulePoll(0); });

async function loadCatalog() {
  try {
    if (mode === 'race') {
      const { genres: catalog } = await request('/api/genres', undefined, null);
      genres = new Map(catalog.map(({ id, name, color }) => [name.toLowerCase(), { id, name, color }]));
      populateGenreOptions($('#genre-options'), genres);
      setText($('#catalog-caption'), `${catalog.length.toLocaleString('en-US')} genres`);
      state.ready = true;
    } else {
      const status = await request('/api/status', undefined, null);
      setText($('#catalog-caption'), `${status.genres.toLocaleString('en-US')} genres`);
      state.ready = status.ready;
      if (!state.ready) throw new Error('The genre catalog is not ready. Please try again shortly.');
    }
    connection();
  } catch (error) {
    connection(error.message || 'The genre list could not load. Please retry.');
    setText($('#catalog-caption'), 'Waiting for the genre catalog');
  } finally { setBusy(false); }
}

async function loadInvite() {
  showPage('join');
  state.preview = null;
  setText($('#join-description'), 'Finding the room…');
  setBusy(true);
  try {
    const preview = await request(roomPath(), undefined, null);
    if (preview.mode !== mode) { location.replace(`/multiplayer-genre${preview.mode}?room=${encodeURIComponent(preview.id)}`); return; }
    state.preview = preview;
    setText($('#join-description'), preview.stage === 'lobby' ? `${(preview.players || []).filter((player) => !player.left).length} players in the lobby. Join them.` : 'This game has already started. Join a new room for the next game.');
    setText($('#join-settings'), settingsSummary(preview));
    connection();
  } catch (error) {
    setText($('#join-description'), 'This invitation could not be opened.');
    if (error.data?.code === 'room_not_found') connection('This room has expired or no longer exists.', true);
    else if (error.data?.code === 'room_started') message('This game has already started. Join a new room for the next game.');
    else connection(error.message || 'The room could not load. Please retry.');
  } finally { setBusy(false); }
}

updateParameters();
$('#player-name').value = storage.get('genre-multiplayer:name') || '';
$('#join-name').value = $('#player-name').value;
if (state.requestedRoom) {
  try { state.credentials = JSON.parse(storage.get(credentialKey(state.requestedRoom)) || 'null'); } catch { state.credentials = null; }
  if (state.credentials?.token && state.credentials?.player_id) {
    showPage('join');
    setText($('#join-description'), 'Reconnecting to your room…');
    try {
      applySnapshot(await request(roomPath()));
      schedulePoll();
    } catch (error) {
      if (error.data?.code === 'invalid_token') {
        storage.remove(credentialKey(state.requestedRoom));
        state.credentials = null;
        await loadInvite();
      } else if (!terminalError(error)) {
        connection('Connection interrupted. Reconnecting to your room…');
        schedulePoll();
      }
    }
  } else { state.credentials = null; await loadInvite(); }
} else { showPage('setup'); await loadCatalog(); }
