const activation = document.body.dataset.activation;
const storageKey = 'wcag-pointer-cancellation-' + activation;
const entries = JSON.parse(localStorage.getItem(storageKey) || '[]');
const render = () => {
  document.querySelector('#count').textContent = String(entries.length);
  document.querySelector('#entries').replaceChildren(...entries.map(text => {
    const item = document.createElement('li');
    item.textContent = text;
    return item;
  }));
};
const commit = () => {
  entries.push('Activity entry ' + (entries.length + 1));
  localStorage.setItem(storageKey, JSON.stringify(entries));
  render();
};
const button = document.querySelector('#append');
if (activation === 'up') {
  button.addEventListener('click', commit);
} else {
  button.addEventListener('pointerdown', event => {
    if (event.isPrimary && event.button === 0) commit();
  });
  // Keep keyboard activation available; this fixture isolates pointer timing.
  button.addEventListener('click', event => { if (event.detail === 0) commit(); });
}
render();
