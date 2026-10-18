import { test } from 'node:test';
import assert from 'node:assert/strict';
import { translate } from '../web/i18n-messages.js';

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
