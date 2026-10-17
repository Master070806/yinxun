import { GenreCluster } from '/genre-cluster.js';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { stage: 'setup', metric: 'xyrgb', count: 4, id: null, retryId: null,
  cluster: null, genre: null, groups: [], finalCluster: null, busy: false, finished: false };
let scenes = [];
let finalScene = null;
let ready = false;
let audioVersion = 0;
let candidateVersion = 0;
let candidateGenre = null;
let audioOwner = null;
const player = document.createElement('audio');
player.id = 'game-audio';
player.preload = 'none';
player.hidden = true;
document.body.append(player);
const candidatePlayer = document.createElement('audio');
candidatePlayer.id = 'candidate-audio';
candidatePlayer.preload = 'none';
candidatePlayer.hidden = true;
document.body.append(candidatePlayer);

async function request(path, payload) {
  const response = await fetch(path, payload === undefined ? { cache: 'no-store' } : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw Object.assign(new Error(data.error || 'Please try again.'), { data });
  return data;
}

function message(text = '') {
  const node = state.stage === 'setup' ? $('#setup-message') : $(`#${state.stage} .game-message`);
  node.textContent = text;
  node.hidden = !text;
}

function disposeScenes() {
  scenes.forEach((scene) => scene.destroy());
  scenes = [];
  finalScene?.destroy();
  finalScene = null;
}

function updateParameters() {
  state.metric = $('input[name=metric]:checked').value;
  state.count = Number($('#cluster-count').value);
  $('#count-value').value = state.count;
  $('#size-value').value = Number($('#cluster-size').value);
  const weight = Number($('#map-weight').value);
  $('#weight-value').value = `${weight} / ${100 - weight}`;
  $$('.metric-parameter').forEach((field) => {
    const active = field.dataset.for.split(' ').includes(state.metric);
    field.hidden = !active;
    field.querySelectorAll('input').forEach((input) => { input.disabled = !active; });
  });
  $('.parameter-grid').classList.toggle('kernel-grid', state.metric === 'kernel');
  $('#separation').max = state.metric === 'kernel' ? '2' : '10';
}

function settings() {
  return { metric: state.metric, count: state.count,
    ...(state.metric !== 'graph' ? { cluster_size: Number($('#cluster-size').value) } : {}),
    alpha: Number($('#map-weight').value) / 100,
    separation: Number($(state.metric === 'graph' ? '#graph-separation' : '#separation').value),
    opposition: Number($('#opposition-weight').value), regularization: Number($('#regularization').value) };
}

function setBusy(busy) {
  state.busy = busy;
  if (busy) stopCandidateAudio();
  $('#arrangement-form').setAttribute('aria-busy', String(busy));
  $$('#arrangement-form fieldset').forEach((field) => { field.disabled = busy; });
  const start = $('#arrangement-form button[type=submit]');
  start.disabled = busy || !ready;
  start.textContent = busy ? 'Preparing…' : state.retryId ? 'Retry game →' : 'Start game →';
  $('#continue-button').disabled = busy || (!state.finished && state.cluster === null);
  $('#confirm-answer').disabled = busy || (!state.finished && state.genre === null);
  $$('#final-viewport button').forEach((button) => { button.disabled = busy || state.finished; });
}

function playerIcon(playing = false) {
  $$('.play-link').forEach((button, index) => {
    button.querySelector('span').textContent = playing ? 'Ⅱ' : '▷';
    button.setAttribute('aria-label', `${playing ? 'Pause' : 'Play'} ${index ? 'second' : 'first'} sample`);
  });
}

function setAudio(source, available = true) {
  stopCandidateAudio();
  audioOwner = null;
  audioVersion++;
  player.pause();
  player.removeAttribute('src');
  if (source && available) player.src = source;
  player.load();
  playerIcon();
  $$('.play-link').forEach((button) => { button.disabled = !source || !available; });
  if (source && !available) message('This sample is unavailable in the source.');
}

async function toggleAudio() {
  if (!player.getAttribute('src')) return;
  stopCandidateAudio();
  audioOwner = 'clue';
  if (!player.paused) { player.pause(); return; }
  const version = audioVersion;
  const button = $(`#${state.stage} .play-link`);
  button.querySelector('span').textContent = '…';
  if (!state.finished) message();
  try {
    if (player.error) player.load();
    await player.play();
  } catch {
    if (version !== audioVersion) return;
    playerIcon();
    if (!state.finished) message('Sample unavailable. Try playing it again.');
  }
}
player.addEventListener('play', () => {
  if (audioOwner !== 'clue') { player.pause(); return; }
  playerIcon(true);
});
player.addEventListener('pause', () => playerIcon());
player.addEventListener('ended', () => playerIcon());
player.addEventListener('error', () => {
  playerIcon();
  if (audioOwner === 'clue' && state.stage !== 'setup' && !state.finished) {
    message('Sample unavailable. Try playing it again.');
  }
});
$$('.play-link').forEach((button) => button.addEventListener('click', toggleAudio));

function candidateIndicator(status = '') {
  finalScene?.items.forEach(({ genre, label }) => {
    const active = genre.id === candidateGenre?.id;
    label.classList.toggle('gc-listening', active && status === 'playing');
    label.classList.toggle('gc-loading', active && status === 'loading');
    label.setAttribute('aria-busy', String(active && status === 'loading'));
  });
}

function stopCandidateAudio() {
  candidateVersion++;
  if (audioOwner === 'candidate') audioOwner = null;
  candidatePlayer.pause();
  candidatePlayer.removeAttribute('src');
  candidatePlayer.load();
  candidateIndicator();
  candidateGenre = null;
}

async function previewGenre(genre) {
  stopCandidateAudio();
  // Invalidate a pending clue play request before changing which audio owns playback.
  audioVersion++;
  audioOwner = 'candidate';
  player.pause();
  playerIcon();
  candidateGenre = genre;
  const version = candidateVersion;
  candidatePlayer.src = `/api/games/${state.id}/candidate/${genre.id}/audio`;
  candidateIndicator('loading');
  message();
  try {
    await candidatePlayer.play();
  } catch {
    if (version !== candidateVersion || state.finished || audioOwner !== 'candidate') return;
    candidateIndicator();
    message(`Sample unavailable for ${genre.name}. Try again.`);
  }
}

candidatePlayer.addEventListener('playing', () => {
  if (audioOwner !== 'candidate' || state.finished) { candidatePlayer.pause(); return; }
  candidateIndicator('playing');
  $('#answer-note').textContent = `${candidateGenre.name} selected. Playing comparison sample.`;
});
candidatePlayer.addEventListener('pause', () => {
  if (candidatePlayer.paused) candidateIndicator();
});
candidatePlayer.addEventListener('ended', () => candidateIndicator());
candidatePlayer.addEventListener('error', () => {
  if (!candidatePlayer.error || audioOwner !== 'candidate' || state.finished || !candidateGenre) return;
  candidateIndicator();
  message(`Sample unavailable for ${candidateGenre.name}. Try again.`);
});

function renderRound() {
  const grid = $('#cluster-grid');
  grid.replaceChildren();
  state.groups.forEach((group, index) => {
    const card = document.createElement('div');
    card.className = 'cluster-card';
    card.tabIndex = 0;
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', `Cluster ${index + 1}: ${group.genres.map(genre => genre.name).join(', ')}`);
    card.setAttribute('aria-pressed', 'false');
    const viewport = document.createElement('div');
    viewport.className = 'cluster-viewport';
    card.append(viewport);
    grid.append(card);
    scenes.push(new GenreCluster(viewport, group.genres));
    const choose = () => {
      if (state.stage !== 'round-one' || state.busy || state.finished) return;
      state.cluster = group.id;
      $$('.cluster-card').forEach((item, i) => {
        item.classList.toggle('is-selected', i === index);
        item.setAttribute('aria-pressed', String(i === index));
      });
      $('#continue-button').disabled = false;
      $('#cluster-choice').textContent = `Cluster ${index + 1} selected.`;
    };
    card.addEventListener('click', choose);
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(); }
    });
  });
  $('#continue-button').textContent = 'Select';
  $('#continue-button').disabled = true;
}

function chooseGenre(name, genre) {
  if (state.stage !== 'final' || state.finished || state.busy) return;
  if (!state.finalCluster.genres.some((item) => item.id === genre.id)) return;
  state.genre = genre.id;
  finalScene.select(name);
  $('#confirm-answer').disabled = false;
  $('#answer-note').textContent = `${name} selected.`;
  previewGenre(genre);
}

function renderFinal() {
  finalScene = new GenreCluster($('#final-viewport'), state.finalCluster.genres, {
    selectable: true, large: true, onSelect: chooseGenre,
  });
  finalScene.items.forEach(({ label }) => { label.title = 'Listen and select'; });
  $('#confirm-answer').textContent = 'Select';
  $('#confirm-answer').disabled = true;
}

function syncAddress() {
  if (location.hash !== `#${state.stage}`) history.replaceState(null, '', `#${state.stage}`);
}

function showStage() {
  stopCandidateAudio();
  disposeScenes();
  const playing = state.stage !== 'setup';
  document.body.classList.toggle('playing', playing);
  $('.site-header').hidden = playing;
  $('.site-footer').hidden = playing;
  $$('.page').forEach((section) => { section.hidden = section.id !== state.stage; });
  $$('.game-message').forEach((node) => { node.hidden = true; node.textContent = ''; });
  $('#cluster-choice').textContent = '';
  $('#answer-note').textContent = '';
  document.title = `${state.stage === 'setup' ? 'Genreguessr' : state.stage === 'round-one' ? 'Round one' : 'Round two'} — Cartography & BGMs`;
  if (state.stage === 'round-one') renderRound();
  if (state.stage === 'final') renderFinal();
  syncAddress();
  window.scrollTo({ top: 0, behavior: 'instant' });
  $(`#${state.stage} h1`).focus({ preventScroll: true });
}

function finish(result) {
  state.finished = true;
  stopCandidateAudio();
  audioVersion++;
  audioOwner = null;
  player.pause();
  message(`${result.correct ? 'Correct' : 'Answer'}: `);
  const answer = $(`#${state.stage} .game-message`);
  if (result.target.url) {
    const link = document.createElement('a');
    link.href = result.target.url;
    link.textContent = result.target.name;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.title = 'View this genre on Every Noise at Once';
    answer.append(link);
  } else {
    answer.append(result.target.name);
  }
  $$('.cluster-card').forEach((card) => { card.setAttribute('aria-disabled', 'true'); card.tabIndex = -1; });
  $$('#final-viewport button').forEach((button) => { button.disabled = true; });
  const button = $(state.stage === 'round-one' ? '#continue-button' : '#confirm-answer');
  button.textContent = 'New game';
}

function newGame() {
  setAudio(null);
  Object.assign(state, { stage: 'setup', id: null, retryId: null, cluster: null, genre: null,
    groups: [], finalCluster: null, finished: false });
  message();
  showStage();
  setBusy(false);
}

$('#arrangement-form').addEventListener('input', updateParameters);
$('#arrangement-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!ready || state.busy || state.stage !== 'setup') return;
  updateParameters();
  const chosenSettings = settings();
  message();
  setBusy(true);
  try {
    const game = await request('/api/games', { settings: chosenSettings, retry_id: state.retryId });
    Object.assign(state, { id: game.id, retryId: null, groups: game.clusters, stage: game.stage,
      cluster: null, genre: null, finished: false });
    showStage();
    setAudio(game.audio, game.audio_available);
  } catch (error) {
    if (error.data?.code === 'game_not_found') {
      state.retryId = null;
      message('This game has expired. Start game will draw a new target.');
      return;
    }
    if (error.data?.retryable && error.data.id) state.retryId = error.data.id;
    message(error.message || 'The game could not start. Please try again.');
  } finally { setBusy(false); }
});

$('#continue-button').addEventListener('click', async () => {
  if (state.busy || state.stage !== 'round-one') return;
  if (state.finished) { newGame(); return; }
  if (state.cluster === null) return;
  message();
  setBusy(true);
  try {
    const result = await request(`/api/games/${state.id}/cluster`, { cluster_id: state.cluster });
    if (result.stage === 'finished') finish(result);
    else {
      state.finalCluster = result.cluster;
      state.stage = result.stage;
      showStage();
      setAudio(result.audio, result.audio_available);
    }
  } catch (error) { message(error.message); }
  finally { setBusy(false); }
});

$('#confirm-answer').addEventListener('click', async () => {
  if (state.busy || state.stage !== 'final') return;
  if (state.finished) { newGame(); return; }
  if (state.genre === null) return;
  message();
  setBusy(true);
  try {
    finish(await request(`/api/games/${state.id}/genre`, { genre_id: state.genre }));
  } catch (error) { message(error.message); }
  finally { setBusy(false); }
});

window.addEventListener('hashchange', syncAddress);
updateParameters();
showStage();
try {
  const status = await request('/api/status');
  ready = status.ready;
  $('#catalog-caption').textContent = `${status.genres.toLocaleString('en-US')} genres`;
  setBusy(false);
} catch {
  $('#load-error').hidden = false;
}
