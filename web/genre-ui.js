import { setText, currentLanguage } from '/i18n.js';
import { chineseGenre, genreLabel } from '/genre-names.js';

export const displayGenre = name => genreLabel(name, currentLanguage());
export function setGenreText(element, name, compact = false) {
  setText(element, language => compact && language !== 'en' ? chineseGenre(name) || name : genreLabel(name, language));
  if (compact) element.title = name;
}

const lists = new Map();
export function populateGenreOptions(container, genres) {
  lists.set(container, genres);
  container.replaceChildren(...[...genres.values()].sort((a, b) => a.name.localeCompare(b.name)).map(genre => {
    const option = document.createElement('option');
    option.value = displayGenre(genre.name);
    return option;
  }));
}
window.addEventListener('languagechange', () => {
  for (const [container, genres] of lists) {
    if (container.isConnected) populateGenreOptions(container, genres);
    else lists.delete(container);
  }
});
