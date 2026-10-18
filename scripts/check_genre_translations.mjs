// Accepts a private names-only JSON array; never publishes source data.
// node scripts/check_genre_translations.mjs /path/to/genre-names.json
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { genreReading, genreLabel, findGenre } from '../web/genre-names.js';

if (!process.argv[2]) throw new Error('Provide a JSON array of source genre names.');
const names = JSON.parse(readFileSync(process.argv[2], 'utf8'));
assert.ok(Array.isArray(names) && names.every(name => typeof name === 'string'));
const genres = new Map(names.map((name, id) => [name.toLowerCase(), {id, name}]));
assert.equal(genres.size, names.length, 'Duplicate canonical names');
const counts = {translated: 0, partial: 0, untranslated: 0};
const remaining = [];
for (const name of names) {
  const reading = genreReading(name);
  counts[reading.kind]++;
  assert.ok(!reading.label.includes('undefined'));
  if (reading.kind !== 'untranslated') assert.match(reading.label, /[\u3400-\u9fff]/u);
  assert.equal(genreLabel(name, 'en'), name);
  assert.equal(findGenre(genres, name).name, name);
  if (reading.kind !== 'translated') remaining.push({name, ...reading});
}
console.log(JSON.stringify({total: names.length, ...counts, remaining}, null, 2));
