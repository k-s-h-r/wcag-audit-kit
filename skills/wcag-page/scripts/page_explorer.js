// Discovery hints supplement the AI's inspection of the actual screenshots.
(() => {
  // Observe short function timers without evaluating their source or changing
  // the callback arguments. A quiet DOM is not proof that all future work ended.
  const nativeTimeout = window.setTimeout, nativeClear = window.clearTimeout;
  const nativeClearInterval = window.clearInterval, timers = new Map();
  let lastChange = performance.now(), untrackedCallbacks = 0;
  let operationMutations = null;
  let dialogGeneration = 0;
  new MutationObserver(records => {
    lastChange = performance.now();
    for (const {attributeName, target} of records) {
      if (attributeName === 'open' && target instanceof HTMLDialogElement) dialogGeneration++;
    }
    if (!operationMutations) return;
    for (const {target} of records) {
      if (operationMutations.size >= 1000) break;
      operationMutations.add(target instanceof Element ? target : target.parentElement);
    }
  }).observe(document,
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
      if (!soon && performance.now()-Math.max(lastChange,start) >= quietMs)
        return result(timers.size || untrackedCallbacks ? 'bounded' : 'quiet');
      await new Promise(resolve => nativeTimeout(resolve,25));
    }
    return result('timeout');
  };
  const events = new WeakMap(), original = EventTarget.prototype.addEventListener;
  const pointerInput = /^(click|dblclick|auxclick|contextmenu|mouse|pointer|touch|(?:got|lost)pointercapture)/;
  const pointerMotion = ['mousemove','mouseover','mouseout','mouseenter','mouseleave',
    'pointermove','pointerrawupdate','pointerover','pointerout','pointerenter','pointerleave','pointercancel',
    'gotpointercapture','lostpointercapture','touchmove','touchcancel'];
  let globalKeyboardListener = false, globalPointerListener = false;
  EventTarget.prototype.addEventListener = function (type, ...args) {
    if ((this === window || this === document) && args[0]?.name !== 'wcagAuditInputListener') {
      if (/^key(down|up|press)$/.test(type)) globalKeyboardListener = true;
      if (pointerInput.test(type)) globalPointerListener = true;
    }
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
  const selector = e => {
    const parts = [];
    const root = e.getRootNode();
    for (let n = e; n; n = n.parentElement) {
      if (n.id && root.querySelectorAll('#' + CSS.escape(n.id)).length === 1) {
        parts.unshift('#' + CSS.escape(n.id));
        break;
      }
      const siblings = n.parentElement?.children || root.children;
      parts.unshift(n.localName + (siblings ? ':nth-child(' + ([...siblings].indexOf(n) + 1) + ')' : ''));
    }
    const path = parts.join(' > ');
    // The host is outside this tree. Playwright can locate its open shadow descendants.
    return root.host ? `${selector(root.host)} ${path}` : path;
  };
  window.__wcagBeginOperation = () => { operationMutations = new Set(); };
  window.__wcagOperationMutations = () => {
    const observed = [...(operationMutations || [])];
    operationMutations = null;
    return {targets: [...new Set(observed.filter(e => e?.isConnected).map(selector))],
      truncated: observed.length >= 1000};
  };
  const visible = e => {
    // Descendants of closed details can have layout boxes without being rendered.
    if (e.checkVisibility && !e.checkVisibility()) return false;
    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return !!(r.width && r.height && s.visibility !== 'hidden' && s.display !== 'none');
  };
  let functionOutput, functionControl;
  window.__wcagFunctionValueAtClick = () => functionOutput?.isConnected ? functionOutput.value.trim() : null;
  const keyboardHandler = target => ['onkeydown', 'onkeypress', 'onkeyup'].some(
    key => typeof target[key] === 'function'
  ) || [...(events.get(target) || [])].some(type => /^key(down|up|press)$/.test(type));
  window.__wcagFunctionOutput = (phase, control) => {
    const outputs = [...document.querySelectorAll('output')].filter(visible);
    if (outputs.length !== 1) return null;
    const [output] = outputs;
    const value = output.value.trim();
    if (!/^-?[0-9]+$/.test(value) || !Number.isSafeInteger(Number(value)) || output.innerText.trim() !== value ||
        output.closest('[inert], [aria-hidden="true" i]') || output.form ||
        output.checkVisibility?.({opacityProperty: true}) === false) return null;
    if (phase === 'after') {
      if (output !== functionOutput || !functionControl?.isConnected) return null;
      control = functionControl;
    } else {
      functionOutput = output;
      functionControl = control;
    }
    const observation = {target: selector(output), value, url: location.href};
    if (control) {
      const ancestors = [];
      let customKeys = keyboardHandler(control);
      for (let parent = control.parentElement; parent; parent = parent.parentElement) {
        ancestors.push(selector(parent));
        customKeys ||= keyboardHandler(parent);
      }
      observation.control_ancestors = ancestors;
      observation.custom_keys = globalKeyboardListener || Boolean(document.querySelector('[accesskey], [aria-keyshortcuts]')) ||
        customKeys || [window, document].some(keyboardHandler);
    }
    return observation;
  };
  const deepestActive = root => {
    let active = root.activeElement;
    while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
    return active;
  };
  const composedParent = e => e.assignedSlot || e.parentElement || e.getRootNode().host;
  window.__wcagDisclosure = (opener, bindFocus) => {
    const id = opener.getAttribute('aria-controls')?.trim();
    const root = opener.getRootNode();
    if (closedRoots || !id || /\s/.test(id) || !document.hasFocus()) return null;
    const matches = root.querySelectorAll('#' + CSS.escape(id));
    if (matches.length !== 1 || matches[0] === opener) return null;
    const panel = matches[0], focus = deepestActive(document);
    if (!focus || focus.matches('iframe,frame')) return null;
    if (bindFocus) window.__wcagExpectedInputTarget = focus;
    let navigation = false;
    for (let ancestor = opener; ancestor; ancestor = composedParent(ancestor)) {
      if (ancestor.matches('nav, [role="navigation"]')) {
        navigation = true;
        break;
      }
    }
    const contentToggle = opener.matches('button, [role="button"]') &&
      !navigation && !opener.matches('[aria-haspopup]:not([aria-haspopup="false" i])') &&
      panel.matches('p, div, section, article, aside, [role="region"]') &&
      !panel.matches('[role]:not([role="region"])');
    let contentVisible = null;
    if (contentToggle) {
      if (getComputedStyle(panel).display === 'none') contentVisible = false;
      else if (visible(panel) && panel.checkVisibility?.({
        opacityProperty: true, visibilityProperty: true, contentVisibilityAuto: true
      }) !== false) contentVisible = true;
    }
    return {
      document: performance.timeOrigin, url: location.href,
      opener: selector(opener), panel: selector(panel), expanded: opener.getAttribute('aria-expanded'),
      visible: visible(panel), focus: selector(focus), focus_within: panel.contains(root.activeElement),
      content_toggle: contentToggle, content_visible: contentVisible
    };
  };
  const visibleModals = () => [...document.querySelectorAll(
    'dialog:modal, [aria-modal="true"]:is([role="dialog"], [role="alertdialog"])')].filter(visible);
  window.__wcagDialogElementVisible = e => e.isConnected && visible(e);
  window.__wcagDialogFocus = () => {
    const active = document.activeElement;
    const modals = visibleModals().map(selector);
    return {
      modals, focus: active && selector(active),
      root_focus: (active === document.body || active === document.documentElement) && !active?.hasAttribute('tabindex'),
      supported: document.hasFocus() && !!active && !closedRoots && !active.shadowRoot?.activeElement &&
        !active.matches('iframe, frame'),
      document_start: performance.timeOrigin, url: location.href
    };
  };
  window.__wcagNestedParentInput = () => {
    const modals = visibleModals();
    const input = document.activeElement;
    if (modals.length !== 1 || closedRoots || globalPointerListener || !document.hasFocus() ||
        !(input instanceof HTMLInputElement) || input.type !== 'text' || input.value || input.form ||
        input.disabled || input.readOnly || !visible(input) || input.matches('[role],[list],[aria-haspopup]') ||
        document.querySelector('iframe,frame')) return null;
    const [parent] = modals;
    const all = [...document.querySelectorAll('*')];
    const other = all.filter(node => node !== parent && node.matches('dialog,[role~="dialog" i],[role~="alertdialog" i]'));
    if (other.length !== 1 || !parent.contains(input) || all.some(node => node.shadowRoot)) return null;
    const [child] = other;
    if (!parent.contains(child) || !child.matches('[hidden][aria-modal="true"]:is([role="dialog"],[role="alertdialog"])') ||
        visible(child)) return null;

    const handlerProperty = (node, types) => types.some(type => typeof node['on' + type] === 'function');
    const pointerHandler = node => [...(events.get(node) || [])].some(type => pointerInput.test(type)) ||
      handlerProperty(node, [...pointerMotion, 'click','dblclick','auxclick','contextmenu','mousedown','mouseup',
       'pointerdown','pointerup','touchstart','touchend']);
    // The next locator click can dispatch movement events on the old pointer target as well.
    if (all.some(node => [...(events.get(node) || [])].some(type => pointerMotion.includes(type)) ||
        handlerProperty(node, pointerMotion))) return null;
    if (pointerHandler(window) || pointerHandler(document)) return null;
    for (let node = input; node; node = node.parentElement) if (pointerHandler(node)) return null;
    return {parent:selector(parent), child:selector(child), focus:selector(input)};
  };
  window.__wcagCombobox = input => {
    const id = input.getAttribute('aria-controls')?.trim();
    const root = input.getRootNode();
    if (!id || /\s/.test(id) || input.getAttribute('role') !== 'combobox' || !document.hasFocus()) return null;
    const panels = root.querySelectorAll('#' + CSS.escape(id));
    if (panels.length > 1 || (panels[0] && panels[0].getAttribute('role') !== 'listbox')) return null;
    const panel = panels[0];
    const bounds = panel?.getBoundingClientRect();
    const shown = !!panel && visible(panel) &&
      panel.checkVisibility?.({opacityProperty: true, visibilityProperty: true, contentVisibilityAuto: true}) !== false &&
      bounds.right > 0 && bounds.bottom > 0 && bounds.left < innerWidth && bounds.top < innerHeight;
    const active = input.getAttribute('aria-activedescendant');
    const options = panel && active ? root.querySelectorAll('#' + CSS.escape(active)) : [];
    const option = options.length === 1 ? options[0] : null;
    return {
      document: performance.timeOrigin, url: location.href, panel_id: id,
      visible: shown, expanded: input.getAttribute('aria-expanded'),
      active_option: shown && option && panel.contains(option) && option.matches('[role=option]') && visible(option)
        ? selector(option) : null,
      focused: input === root.activeElement, value: input.type === 'password' ? null : input.value
    };
  };
  const relationAttributes = new Set(['aria-controls', 'aria-owns', 'aria-labelledby',
    'aria-describedby', 'aria-activedescendant', 'aria-details', 'aria-errormessage', 'for']);
  const nameAttributes = new Set(['aria-labelledby', 'aria-describedby', 'aria-errormessage']);
  const operationSnapshot = (all, roots, includeRelations) => {
    const idCounts = new Map();
    for (const e of all) if (e.id) idCounts.set(e.id, (idCounts.get(e.id) || 0) + 1);
    const hiddenCache = new WeakMap();
    const hasHiddenAncestor = e => {
      if (!e) return false;
      if (!hiddenCache.has(e)) {
        const css = getComputedStyle(e);
        hiddenCache.set(e, css.display === 'none' || css.contentVisibility === 'hidden' ||
          e.matches('[inert], [aria-hidden="true" i]') || hasHiddenAncestor(e.parentElement));
      }
      return hiddenCache.get(e);
    };
    const inputs = {};
    const relations = [];
    const references = {};
    const reusable = document.compatMode === 'CSS1Compat' && roots.length === 1 &&
      closedRoots === 0 && !document.querySelector('iframe,frame');
    for (const e of all) {
      if (includeRelations) {
        for (const attribute of e.getAttributeNames().filter(name => relationAttributes.has(name))) {
          for (const id of e.getAttribute(attribute).split(/\s+/).filter(Boolean)) {
            const target = e.getRootNode().getElementById(id);
            if (!target) continue;
            const name = selector(target);
            relations.push([selector(e), name, attribute]);
            if (nameAttributes.has(attribute) && !(name in references)) {
              references[name] = JSON.stringify([target.textContent, target.getAttribute('aria-label')]);
            }
          }
        }
      }
      // Only plain, visible HTML with stable axe targets can reuse element-local results.
      // Focus, naming, and widget-level checks keep their whole-document context.
      if (!reusable || !/^[A-Za-z_][\w-]*$/.test(e.id) || idCounts.get(e.id) !== 1 ||
        e.namespaceURI !== 'http://www.w3.org/1999/xhtml' ||
        e.closest('area, details, noscript, template, select, object, canvas, audio, video') ||
        !(e.hasAttribute('tabindex') || e.getAttributeNames().some(name => name.startsWith('aria-'))) ||
        !visible(e) || getComputedStyle(e).visibility === 'collapse' || hasHiddenAncestor(e)) continue;
      const html = e.outerHTML;
      if (html.length <= 4096) inputs['#' + e.id] = html;
    }
    return {operation_inputs: inputs, operation_relations: relations, operation_reference_inputs: references,
      operation_scope_supported: reusable};
  };
  window.__wcagExplore = (operationEvidence = false) => {
    if (operationEvidence === 'native-modal-state')
      return {selectors:[...document.querySelectorAll('dialog:modal')].map(selector), generation:dialogGeneration};
    const all = [], roots = [document];
    for (let i = 0; i < roots.length; i++) for (const e of roots[i].querySelectorAll('*')) {
      all.push(e); if (e.shadowRoot) roots.push(e.shadowRoot);
    }
    if (operationEvidence === 'inputs') return operationSnapshot(all, roots, false);
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
      styles:['color','backgroundColor'].map(k => getComputedStyle(e)[k]),
      attributes:[...e.attributes].filter(a => /^(aria-.*|alt|title|lang|dir|for|id|class|style|tabindex)$/.test(a.name))
        .map(a => [a.name, a.value]).sort(([a], [b]) => a < b ? -1 : Number(a > b))
    }));
    const operation = operationEvidence ? operationSnapshot(all, roots, true) : {};
    const focused = deepestActive(document);
    if (operationEvidence) operation.operation_focus = focused ? selector(focused) : '';
    if (operationEvidence === 'before') return {...operation, state, url: location.href};
    const horizontalTab = e => {
      if (e?.getAttribute('role') !== 'tab') return false;
      const list = e.closest('[role="tablist"]');
      const orientation = list?.getAttribute('aria-orientation');
      return orientation === null || orientation === 'horizontal';
    };
    const focusedTab = horizontalTab(focused) && visible(focused) ? selector(focused) : null;
    const recordedFocus = focusedTab ? focused : document.activeElement;
    const modal = all.filter(e => (e.matches('dialog[open]') || e.getAttribute('aria-modal') === 'true') && visible(e)).at(-1);
    const activeModals = visibleModals();
    const nativeModals = all.filter(e => e.localName === 'dialog' && e.matches(':modal')).map(selector);
    const singleModal = activeModals.length === 1 ? activeModals[0] : null;
    const properties=['onclick','onmousedown','onpointerdown','onpointerup','onpointerenter','onmouseover','onkeydown','onchange','oninput'];
    const eligible = all.filter(e => visible(e) && (!modal || e === modal || modal.contains(e)) &&
      !e.matches(':disabled') && e.getAttribute('aria-disabled') !== 'true');
    const semanticControl = e => e.matches('button,a[href],input,select,textarea,summary,[contenteditable=true]') ||
      /^(button|combobox|listbox|option|tab|checkbox|radio|menuitem|slider|switch|treeitem)$/.test(e.getAttribute('role'));
    // Negative tabindex also marks passive programmatic focus destinations.
    const explicitControls = new Set(eligible.filter(e =>
      semanticControl(e) || e.matches('[onclick],[onmouseover]') ||
      (e.hasAttribute('tabindex') && e.tabIndex >= 0) ||
      properties.some(p => typeof e[p] === 'function') ||
      [...(events.get(e) || [])].some(t => /click|pointer|mouse|key|change|input/.test(t))));
    const inheritsControlCursor = e => {
      for (let ancestor = composedParent(e); ancestor; ancestor = composedParent(ancestor)) {
        if (getComputedStyle(ancestor).cursor !== 'pointer') return false;
        if (semanticControl(ancestor)) return true;
      }
      return false;
    };
    const pointerOnly = eligible.filter(e => !explicitControls.has(e) && getComputedStyle(e).cursor === 'pointer' &&
      (e.style?.cursor === 'pointer' || !inheritsControlCursor(e)));
    const controls = [...explicitControls, ...pointerOnly]
      .filter(e => !(e.getAttribute('role') === 'listbox' && e.tabIndex < 0 && e.id &&
        all.some(c => c.getAttribute('role') === 'combobox' && (c.getAttribute('aria-controls') || '').split(/\s+/).includes(e.id))))
      .map(e => {
        const r = e.getBoundingClientRect();
        return {selector:selector(e), tag:e.localName, role:e.getAttribute('role'), type:e.type || e.getAttribute('type'),
          formAssociated:e.form instanceof HTMLFormElement,
          label:e.getAttribute('aria-label') || e.labels?.[0]?.innerText || e.innerText?.trim().slice(0,160) || e.getAttribute('placeholder') || e.id,
          href:e.getAttribute('href'), expanded:e.getAttribute('aria-expanded'), tabIndex:e.tabIndex,
          haspopup:e.getAttribute('aria-haspopup'), events:[...(events.get(e) || []),...properties.filter(p => typeof e[p] === 'function')],
          ...(horizontalTab(e) ? {horizontalTab:true} : {}),
          ...(singleModal?.contains(e) && e.matches('button,input[type="button"],[role="button"]')
            ? {buttonInModal:true} : {}),
          rect:{x:r.x + scrollX,y:r.y + scrollY,width:r.width,height:r.height}};
      });
    return {...operation,url:location.href,title:document.title,controls,state,modal:modal ? selector(modal) : null,
      ...(nativeModals.length ? {native_modals:nativeModals} : {}),
      dialog_generation:dialogGeneration,
      frames:all.filter(e => e.matches('iframe,frame')).map(selector), closedRoots,
      canvases:all.filter(e => e.localName === 'canvas' && visible(e)).map(selector),
      scroll:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight},
      ...(focusedTab ? {focused_horizontal_tab:focusedTab} : {}),
      ...(focused && focused !== recordedFocus ? {deep_focus:selector(focused)} : {}),
      focus:{selector:recordedFocus ? selector(recordedFocus) : '',text:recordedFocus?.innerText?.slice(0,160),
        outline:recordedFocus ? ['outlineStyle','outlineWidth','outlineColor'].map(k => getComputedStyle(recordedFocus)[k]) : []}};
  };
})();
