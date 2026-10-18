import { setText, setAttr } from '/i18n.js';
import { GenreCluster } from '/genre-cluster.js';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { stage: 'setup', id: null, route: [], current: null, goal: null,
  cluster: null, settings: null, selected: null, moves: 0, revision: 0,
  goalReachable: true, busy: false };
let genres = new Map();
let scene = null;
let ready = false;
let audioVersion = 0;
const player = document.createElement('audio');
player.id = 'race-audio';
player.preload = 'none';
player.hidden = true;
document.body.append(player);

async function request(path, payload) {
  const response = await fetch(path, payload === undefined ? { cache: 'no-store' } : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw Object.assign(new Error(data.error || 'Please try again.'), { data });
  return data;
}

function message(text = '') {
  setText($('#setup-message'), text);
  $('#setup-message').hidden = !text;
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
}

function settings() {
  const metric = $('input[name=metric]:checked').value;
  if (metric === 'graph') return { metric, radius: 1 };
  const values = { metric, cluster_size: Number($('#cluster-size').value) };
  if (metric === 'xyrgb') values.alpha = Number($('#map-weight').value) / 100;
  else Object.assign(values, {
    opposition: Number($('#opposition-weight').value),
    regularization: Number($('#regularization').value),
  });
  return values;
}

function setBusy(busy) {
  state.busy = busy;
  $('#race-form').setAttribute('aria-busy', String(busy));
  $$('#race-form fieldset').forEach((fieldset) => { fieldset.disabled = busy; });
  $$('.randomize-genre').forEach((button) => { button.disabled = busy || !ready; });
  $('#start-race').disabled = busy || !ready;
  setText($('#start-race'), busy && state.stage === 'setup' ? 'Preparing…' : 'Start race →');
  $('#confirm-move').disabled = busy || !state.selected || state.selected.id === state.current?.id;
  $$('#race-viewport button').forEach((button) => { button.disabled = busy; });
}

function syncAddress() {
  if (location.hash !== `#${state.stage}`) history.replaceState(null, '', `#${state.stage}`);
}

function showStage(stage) {
  stopAudio();
  state.stage = stage;
  scene?.destroy();
  scene = null;
  $$('.page').forEach((page) => { page.hidden = page.id !== stage; });
  $('.site-header').hidden = stage !== 'setup';
  $('.site-footer').hidden = stage !== 'setup';
  document.body.classList.toggle('playing', stage === 'race');
  document.body.classList.toggle('won', stage === 'win');
  setText(document.querySelector('title'), `${stage === 'win' ? 'You win — ' : ''}Genrerace — Cartography & BGMs`);
  syncAddress();
  window.scrollTo({ top: 0, behavior: 'instant' });
  $(`#${stage}-title`).focus({ preventScroll: true });
}

function renderCluster() {
  stopAudio();
  state.selected = null;
  $('#confirm-move').disabled = true;
  playbackMessage();
  scene?.destroy();
  scene = new GenreCluster($('#race-viewport'), state.cluster.genres, {
    selectable: true, large: true, onSelect: selectGenre,
  });
  for (const { genre, label } of scene.items) {
    if (genre.id === state.current.id) {
      label.classList.add('race-current');
      label.setAttribute('aria-current', 'location');
      setAttr(label, 'aria-label', `${genre.name}, current genre`);
    }
    setAttr(label, 'title', `Listen to ${genre.name}`);
  }
  setText($('#race-announcement'), `At ${state.current.name}. Goal: ${state.goal.name}. ${state.moves} ${state.moves === 1 ? 'move' : 'moves'}.`);
  $('#race-title').focus({ preventScroll: true });
}

function renderTrace() {
  setText($('#trace-count'), `${state.moves} ${state.moves === 1 ? 'move' : 'moves'}`);
  $('#race-trace').replaceChildren(...state.route.map((genre, index) => {
    const stop = document.createElement('li');
    if (index > 0) {
      const separator = document.createElement('span');
      separator.className = 'trace-separator';
      setText(separator, '→');
      separator.setAttribute('aria-hidden', 'true');
      stop.append(separator);
    }
    const name = document.createElement('span');
    name.className = 'trace-genre';
    name.textContent = genre.name;
    name.style.color = genre.color;
    if (index === state.route.length - 1) name.setAttribute('aria-current', 'location');
    stop.append(name);
    return stop;
  }));
}

function applyRace(race) {
  Object.assign(state, { id: race.id, route: race.route, current: race.current,
    goal: race.goal, cluster: race.cluster, settings: race.settings,
    moves: race.moves, revision: race.revision, goalReachable: race.goal_reachable,
    selected: null });
  if (race.stage === 'win') {
    showStage('win');
    setText($('#round-count'), `${state.moves} ${state.moves === 1 ? 'round' : 'rounds'}`);
    $('#visited-route').replaceChildren(...state.route.map((genre) => {
      const stop = document.createElement('li');
      const name = document.createElement('span');
      name.textContent = genre.name;
      name.style.color = genre.color;
      stop.append(name);
      return stop;
    }));
  } else {
    if (state.stage !== 'race') showStage('race');
    $('#race-goal-name').textContent = state.goal.name;
    $('#race-goal-name').style.color = state.goal.color;
    renderTrace();
    renderCluster();
  }
}

async function move() {
  const genre = state.selected;
  if (state.stage !== 'race' || state.busy || !genre || genre.id === state.current.id) return;
  if (!scene.items.some((item) => item.genre.id === genre.id)) return;
  const revision = state.revision;
  stopAudio();
  playbackMessage();
  setBusy(true);
  try {
    applyRace(await request(`/api/races/${state.id}/move`, { genre_id: genre.id, revision }));
  } catch (error) {
    // A retry after a lost response must resync, never count the same move twice.
    if (error.data?.race) applyRace(error.data.race);
    if (state.stage === 'race') playbackMessage(error.message || 'The move could not be saved. Please try again.');
  } finally { setBusy(false); }
}

function playbackMessage(text = '') {
  const value = text || (state.stage === 'race' && !state.goalReachable ? 'The goal is unreachable from this genre.' : '');
  setText($('#race-message'), value);
  $('#race-message').hidden = !value;
}

function playbackIndicator(status = '') {
  scene?.items.forEach(({ genre, label }) => {
    const selected = genre.id === state.selected?.id;
    label.classList.toggle('gc-loading', selected && status === 'loading');
    label.classList.toggle('gc-listening', selected && status === 'playing');
    label.setAttribute('aria-busy', String(selected && status === 'loading'));
  });
}

function stopAudio() {
  audioVersion++;
  player.pause();
  player.removeAttribute('src');
  player.load();
  playbackIndicator();
}

async function selectGenre(name, genre) {
  if (state.stage !== 'race' || state.busy || !scene.items.some((item) => item.genre.id === genre.id)) return;
  stopAudio();
  state.selected = genre;
  scene.select(name);
  const current = genre.id === state.current.id;
  $('#confirm-move').disabled = current;
  setText($('#race-announcement'), current ? `Listening to ${name}, your current genre.` : `${name} selected. Select to move.`);
  playbackMessage();
  playbackIndicator('loading');
  player.src = `/api/genres/${genre.id}/audio`;
  const version = audioVersion;
  try {
    await player.play();
  } catch {
    if (version !== audioVersion || state.stage !== 'race') return;
    playbackIndicator();
    playbackMessage('Sample unavailable. Try playing it again.');
  }
}

player.addEventListener('playing', () => {
  if (state.stage !== 'race' || !player.getAttribute('src')) { player.pause(); return; }
  playbackIndicator('playing');
});
player.addEventListener('pause', () => { if (player.paused) playbackIndicator(); });
player.addEventListener('ended', () => playbackIndicator());
player.addEventListener('error', () => {
  if (state.stage !== 'race' || !player.error || !player.getAttribute('src')) return;
  playbackIndicator();
  playbackMessage('Sample unavailable. Try playing it again.');
});
$('#confirm-move').addEventListener('click', move);

$('#race-form').addEventListener('input', updateParameters);
$$('.randomize-genre').forEach((button) => {
  button.addEventListener('click', () => {
    if (!ready || state.busy) return;
    const choices = [...genres.values()];
    const genre = choices[Math.floor(Math.random() * choices.length)];
    const input = document.getElementById(button.dataset.input);
    input.value = genre.name;
    message();
    setText($('#randomization-status'), `${input.name === 'start' ? 'Start' : 'Goal'}: ${genre.name}.`);
  });
});
$('#race-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!ready || state.busy || state.stage !== 'setup') return;
  const start = genres.get($('#start-genre').value.trim().toLowerCase());
  const goal = genres.get($('#goal-genre').value.trim().toLowerCase());
  if (!start || !goal) {
    message('Choose a genre from the suggestions.');
    $(!start ? '#start-genre' : '#goal-genre').focus();
    return;
  }
  message();
  const chosenSettings = settings();
  setBusy(true);
  try {
    applyRace(await request('/api/races', { start_id: start.id, goal_id: goal.id, settings: chosenSettings }));
  } catch (error) {
    message(error.message || 'The race could not start. Please try again.');
  } finally { setBusy(false); }
});
window.addEventListener('hashchange', syncAddress);
updateParameters();
showStage('setup');

try {
  const { genres: catalog } = await request('/api/genres');
  genres = new Map(catalog.map(({ id, name, color }) => [name.toLowerCase(), { id, name, color }]));
  $('#genre-options').replaceChildren(...[...genres.values()]
    .sort((a, b) => a.name.localeCompare(b.name)).map((genre) => {
      const option = document.createElement('option');
      option.value = genre.name;
      return option;
    }));
  setText($('#catalog-caption'), `${catalog.length.toLocaleString('en-US')} genres`);
  ready = true;
  setBusy(false);
} catch {
  message('The genre list could not load. Please refresh to try again.');
}
