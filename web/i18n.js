import { translate as localize } from '/i18n-messages.js';

const key = 'yinxun-language';
let language = 'zh-CN';
try { if (localStorage.getItem(key) === 'en') language = 'en'; } catch { /* Still usable without storage. */ }
const texts = new Map();
const attributes = new Map();

export const translate = (source) => localize(source, language);
export const currentLanguage = () => language;

export function setText(element, source) {
  // Bind the text node, not the container: appended answer links survive a switch.
  const text = document.createTextNode(translate(source));
  element.replaceChildren(text);
  texts.set(text, source);
  if (texts.size > 400) queueMicrotask(prune);
}

export function setAttr(element, name, source) {
  element.setAttribute(name, translate(source));
  if (!attributes.has(element)) attributes.set(element, new Map());
  attributes.get(element).set(name, source);
}

function prune() {
  for (const node of texts.keys()) if (!node.isConnected) texts.delete(node);
  for (const node of attributes.keys()) if (!node.isConnected) attributes.delete(node);
}

function setLanguage(value) {
  language = value === 'en' ? 'en' : 'zh-CN';
  try { localStorage.setItem(key, language); } catch { /* Session-only preference. */ }
  document.documentElement.lang = language;
  prune();
  for (const [node, source] of texts) node.data = translate(source);
  for (const [node, entries] of attributes) for (const [name, source] of entries) node.setAttribute(name, translate(source));
  switcher.textContent = language === 'zh-CN' ? '中 / EN' : 'EN / 中';
  switcher.setAttribute('aria-label', language === 'zh-CN' ? '切换为英文 / Switch to English' : 'Switch to Chinese / 切换为中文');
  switcher.title = language === 'zh-CN' ? '切换为英文' : 'Switch to Chinese';
  window.dispatchEvent(new Event('languagechange'));
}

// Capture static copy once before game modules render dynamic content.
const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
while (walker.nextNode()) {
  const node = walker.currentNode;
  if (!node.parentElement.closest('script, style, noscript') && node.data.trim()) texts.set(node, node.data);
}
document.querySelectorAll('[aria-label], [placeholder], [title]').forEach((element) => {
  for (const name of ['aria-label', 'placeholder', 'title']) {
    if (element.hasAttribute(name)) setAttr(element, name, element.getAttribute(name));
  }
});
const switcher = document.createElement('button');
switcher.id = 'language-switch';
switcher.type = 'button';
switcher.addEventListener('click', () => setLanguage(language === 'en' ? 'zh-CN' : 'en'));
document.body.append(switcher);
setLanguage(language);
window.addEventListener('storage', (event) => {
  if (event.key === key) setLanguage(event.newValue);
});
