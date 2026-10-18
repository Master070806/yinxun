import { test } from 'node:test';
import assert from 'node:assert/strict';
import { translate } from '../web/i18n-messages.js';
import { chineseGenre, genreReading, genreLabel, findGenre } from '../web/genre-names.js';

test('genre aliases preserve original identifiers and switch back to English', () => {
  assert.equal(genreLabel('russian synthpop'), '俄罗斯合成器流行 · russian synthpop');
  assert.equal(genreLabel('russian synthpop', 'en'), 'russian synthpop');
  assert.equal(chineseGenre('swedish tropical house'), '瑞典热带浩室');
  assert.equal(chineseGenre('instrumental grime'), 'Grime 器乐');
  assert.equal(chineseGenre('imaginary rock'), null);
  assert.equal(genreLabel('imaginary rock'), 'imaginary（摇滚相关） · imaginary rock');
});

test('regional suffixes and multilingual names retain their musical meaning', () => {
  assert.equal(chineseGenre('reggaeton colombiano'), '哥伦比亚雷鬼顿');
  assert.equal(chineseGenre('indie rock italiano'), '意大利独立摇滚');
  assert.equal(chineseGenre('new jersey post-hardcore'), '新泽西后硬核');
  assert.equal(chineseGenre('korean bl ost'), '韩国男同性恋题材影视原声');
  assert.equal(chineseGenre('chicago house'), '芝加哥浩室');
  assert.equal(chineseGenre('guzheng'), '古筝');
  assert.equal(chineseGenre('musique pour enfants'), '儿童音乐');
});

test('partial hints do not fabricate definitions for opaque names', () => {
  assert.deepEqual(genreReading('unfamiliar jazz'), {kind: 'partial', label: 'unfamiliar（爵士相关）'});
  assert.deepEqual(genreReading('swedish unfamiliar'), {kind: 'partial', label: '瑞典音乐 · unfamiliar'});
  assert.deepEqual(genreReading('completely-opaque'), {kind: 'untranslated', label: 'completely-opaque'});
  assert.equal(genreReading('traprun').kind, 'untranslated');
  assert.equal(genreReading('popping').kind, 'translated');
  assert.equal(genreLabel('swedish unfamiliar', 'en'), 'swedish unfamiliar');
  for (const name of ['constructor', 'toString', '__proto__']) assert.equal(chineseGenre(name), null);
});

test('partial hints remain searchable without changing the canonical answer', () => {
  const original = {id: 4, name: 'unfamiliar jazz'};
  const genres = new Map([[original.name, original]]);
  assert.equal(findGenre(genres, 'unfamiliar（爵士相关）'), original);
  assert.equal(findGenre(genres, genreLabel(original.name)), original);
});

test('Chinese and bilingual search return original genre records, ambiguous aliases do not', () => {
  const russian = {id: 11, name: 'russian synthpop'};
  const genres = new Map([['russian synthpop', russian], ['british rock', {id: 12, name: 'british rock'}], ['uk rock', {id: 13, name: 'uk rock'}]]);
  for (const query of ['俄罗斯合成器流行', '俄罗斯合成器流行 · russian synthpop', 'RUSSIAN SYNTHPOP']) {
    assert.equal(findGenre(genres, query), russian);
  }
  assert.equal(findGenre(genres, '英国摇滚'), undefined);
  assert.equal(findGenre(genres, '英国摇滚 · uk rock').id, 13);
});

test('English can be restored from the source, including whitespace', () => {
  assert.equal(translate(' Select '), ' 确认选择 ');
  assert.equal(translate(' Select ', 'en'), ' Select ');
  assert.equal(translate('An unknown upstream error'), 'An unknown upstream error');
});
test('dynamic rounds, waiting and accessible labels translate', () => {
  assert.equal(translate('Round 2 of 5 · Stage 1 of 2'), '第 2 / 5 回合 · 阶段 1 / 2');
  assert.equal(translate('Your choice is in. Waiting for Alice, Bob.'), '选择已提交。等待 Alice, Bob。');
  assert.equal(translate('Cluster 3: piano blues, jazz'), '区域 3：piano blues, jazz');
  assert.equal(translate('Play second sample'), '播放第二段音乐');
  assert.equal(translate('6,291 genres'), '6,291 种风格');
});
test('player and genre names inside messages are preserved, even replacement syntax', () => {
  assert.equal(translate('Listen to $& synthpop'), '试听 $& synthpop');
  assert.equal(translate('Remove Host from the room'), '将 Host 移出房间');
  const name = lang => `Ready${lang === 'en' ? ' (you)' : '（你）'}`;
  assert.equal(translate(name), 'Ready（你）');
  assert.equal(translate(name, 'en'), 'Ready (you)');
});
test('compound labels and recovery messages are translated', () => {
  assert.equal(translate('Multiplayer Genreguessr — Cartography & BGMs'), '多人听音猜风格 — Cartography & BGMs');
  assert.equal(translate('XYRGB · 5 rounds · 3 clusters'), 'XYRGB · 5 回合 · 3 个区域');
  assert.equal(translate('Checking your submitted answer…'), '正在确认已提交的答案…');
});
