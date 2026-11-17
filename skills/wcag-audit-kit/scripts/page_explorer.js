// Discovery hints supplement the AI's inspection of the actual screenshots.
(() => {
  // Observe short function timers without evaluating their source or changing
  // the callback arguments. A quiet DOM is not proof that all future work ended.
  const nativeTimeout = window.setTimeout, nativeClear = window.clearTimeout;
  const nativeClearInterval = window.clearInterval, timers = new Map();
  let lastChange = performance.now(), untrackedCallbacks = 0;
  new MutationObserver(() => { lastChange = performance.now(); }).observe(document,
    {subtree:true,childList:true,attributes:true,characterData:true});
  window.setTimeout = function (callback, delay, ...args) {
    if (typeof callback !== 'function') {
      untrackedCallbacks++;
      return nativeTimeout.call(this, callback, delay, ...args);
    }
    const milliseconds = Number(delay) || 0;
    let id;
    id = nativeTimeout.call(this, function (...values) {
      timers.delete(id);
      return callback.apply(this, values);
    }, milliseconds, ...args);
    timers.set(id, performance.now() + Math.max(0, milliseconds));
    return id;
  };
  window.clearTimeout = function (id) { timers.delete(id); return nativeClear.call(this,id); };
  window.clearInterval = function (id) { timers.delete(id); return nativeClearInterval.call(this,id); };
  window.__wcagWaitForUpdates = async () => {
    const start = performance.now(), deadline = start + 1500, quietMs = 150;
    const result = status => ({status,elapsed_ms:performance.now()-start,pending_timers:timers.size,
      untracked_callbacks:untrackedCallbacks,scope:'DOM and function timeouts; excludes intervals, network, media and animations'});
    while (performance.now() < deadline) {
      const soon = [...timers.values()].some(due => due <= deadline);
      if (!soon && performance.now()-lastChange >= quietMs)
        return result(timers.size || untrackedCallbacks ? 'bounded' : 'quiet');
      await new Promise(resolve => nativeTimeout(resolve,25));
    }
    return result('timeout');
  };
  const events = new WeakMap(), original = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function (type, ...args) {
    if (this instanceof Element) {
      const types = events.get(this) || new Set(); types.add(type); events.set(this, types);
    }
    return original.call(this, type, ...args);
  };
  let closedRoots = 0;
  const attach = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function (options) {
    if (options.mode === 'closed') closedRoots++;
    return attach.call(this, options);
  };
  window.__wcagExplore = () => {
    const all = [], roots = [document];
    for (let i = 0; i < roots.length; i++) for (const e of roots[i].querySelectorAll('*')) {
      all.push(e); if (e.shadowRoot) roots.push(e.shadowRoot);
    }
    const selector = e => {
      const parts = [];
      for (let n = e; n; n = n.parentElement || n.getRootNode().host) {
        if (n.id && n.getRootNode().querySelectorAll('#' + CSS.escape(n.id)).length === 1) {
          parts.unshift('#' + CSS.escape(n.id));
          const host = n.getRootNode().host;
          if (host) parts.unshift(selector(host));
          break;
        }
        const siblings = n.parentElement?.children || n.getRootNode().children;
        parts.unshift(n.localName + (siblings ? ':nth-child(' + ([...siblings].indexOf(n) + 1) + ')' : ''));
      }
      return parts.join(' ');
    };
    const visible = e => {
      const r = e.getBoundingClientRect(), s = getComputedStyle(e);
      return !!(r.width && r.height && s.visibility !== 'hidden' && s.display !== 'none');
    };
    const modal = all.filter(e => (e.matches('dialog[open]') || e.getAttribute('aria-modal') === 'true') && visible(e)).at(-1);
    const properties=['onclick','onmousedown','onpointerdown','onpointerenter','onmouseover','onkeydown','onchange','oninput'];
    const controls = all.filter(e => visible(e) && (!modal || e === modal || modal.contains(e)) &&
      (e.matches('button,a[href],input,select,textarea,summary,[contenteditable=true],[tabindex],[onclick],[onmouseover]') ||
        /^(button|combobox|listbox|option|tab|checkbox|radio|menuitem|slider|switch|treeitem)$/.test(e.getAttribute('role')) ||
        getComputedStyle(e).cursor === 'pointer' || properties.some(p => typeof e[p] === 'function') ||
        [...(events.get(e) || [])].some(t => /click|pointer|mouse|key|change|input/.test(t))))
      .filter(e => !e.matches(':disabled') && e.getAttribute('aria-disabled') !== 'true')
      .filter(e => !(e.getAttribute('role') === 'listbox' && e.tabIndex < 0 && e.id &&
        all.some(c => c.getAttribute('role') === 'combobox' && (c.getAttribute('aria-controls') || '').split(/\s+/).includes(e.id))))
      .map(e => {
        const r = e.getBoundingClientRect();
        return {selector:selector(e), tag:e.localName, role:e.getAttribute('role'), type:e.type || e.getAttribute('type'),
          formAssociated:e.form instanceof HTMLFormElement,
          label:e.getAttribute('aria-label') || e.labels?.[0]?.innerText || e.innerText?.trim().slice(0,160) || e.getAttribute('placeholder') || e.id,
          href:e.getAttribute('href'), expanded:e.getAttribute('aria-expanded'), tabIndex:e.tabIndex,
          haspopup:e.getAttribute('aria-haspopup'), events:[...(events.get(e) || []),...properties.filter(p => typeof e[p] === 'function')],
          rect:{x:r.x + scrollX,y:r.y + scrollY,width:r.width,height:r.height}};
      });
    const state = all.filter(visible).map(e => ({selector:selector(e), tag:e.localName,
      text:[...e.childNodes].filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent).join('').trim(),
      expanded:e.getAttribute('aria-expanded'), checked:e.checked ?? e.getAttribute('aria-checked'),
      selected:e.getAttribute('aria-selected'), open:e.open, value:(e.type === 'password' ? '[redacted]' : 'value' in e ? e.value : null),
      role:e.getAttribute('role'), hidden:e.getAttribute('aria-hidden'),
      disabled:e.matches(':disabled'), ariaDisabled:e.getAttribute('aria-disabled'),
      readOnly:e.readOnly ?? null, inert:!!e.inert, tabIndex:e.tabIndex,
      type:e.type || e.getAttribute('type'), formAssociated:e.form instanceof HTMLFormElement,
      href:e.getAttribute('href'), contentEditable:e.getAttribute('contenteditable'),
      ariaControls:e.getAttribute('aria-controls'), ariaOwns:e.getAttribute('aria-owns'),
      ariaHasPopup:e.getAttribute('aria-haspopup'), ariaPressed:e.getAttribute('aria-pressed'),
      ariaChecked:e.getAttribute('aria-checked'), ariaActiveDescendant:e.getAttribute('aria-activedescendant'),
      ariaModal:e.getAttribute('aria-modal'),
      styles:['color','backgroundColor'].map(k => getComputedStyle(e)[k])}));
    return {url:location.href,title:document.title,controls,state,modal:modal ? selector(modal) : null,
      frames:all.filter(e => e.matches('iframe,frame')).map(selector), closedRoots,
      canvases:all.filter(e => e.localName === 'canvas' && visible(e)).map(selector),
      scroll:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight},
      focus:{selector:document.activeElement ? selector(document.activeElement) : '',text:document.activeElement?.innerText?.slice(0,160),
        outline:document.activeElement ? ['outlineStyle','outlineWidth','outlineColor'].map(k => getComputedStyle(document.activeElement)[k]) : []}};
  };
})();
