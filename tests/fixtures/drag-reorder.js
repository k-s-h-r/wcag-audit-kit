const list = document.querySelector('#records');
let dragged = null;
function update() {
  const items = [...list.children];
  document.querySelector('#order').value = items.map(item => item.querySelector('span').textContent).join(', ');
  for (const [index, item] of items.entries()) {
    const up = item.querySelector(`#${item.id}-up`);
    const down = item.querySelector(`#${item.id}-down`);
    if (up) up.disabled = index === 0;
    if (down) down.disabled = index === items.length - 1;
  }
}
function move(item, direction) {
  const sibling = direction < 0 ? item.previousElementSibling : item.nextElementSibling;
  if (!sibling) return;
  if (direction < 0) list.insertBefore(item, sibling);
  else list.insertBefore(sibling, item);
  update();
}
for (const item of list.children) {
  item.addEventListener('dragstart', event => {
    dragged = item;
    event.dataTransfer.setData('text/plain', item.id);
    event.dataTransfer.effectAllowed = 'move';
  });
  item.addEventListener('dragover', event => { event.preventDefault(); event.dataTransfer.dropEffect = 'move'; });
  item.addEventListener('drop', event => {
    event.preventDefault();
    if (!dragged || dragged === item) return;
    const items = [...list.children];
    move(dragged, items.indexOf(dragged) < items.indexOf(item) ? 1 : -1);
  });
  item.addEventListener('dragend', () => { dragged = null; });
  item.addEventListener('keydown', event => {
    if (event.target !== item || !['ArrowUp', 'ArrowDown'].includes(event.key)) return;
    event.preventDefault();
    move(item, event.key === 'ArrowUp' ? -1 : 1);
    // Application focus restoration, as a result of a genuine key operation.
    item.focus();
  });
  for (const [suffix, direction] of [['up', -1], ['down', 1]]) {
    item.querySelector(`#${item.id}-${suffix}`)?.addEventListener('click', () => move(item, direction));
  }
}
update();
