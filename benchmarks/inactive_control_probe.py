"""Observe native inactivity on a narrowly scoped, scriptless contrast fixture."""

import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil

CHECKPOINT = '1.4.3-01'
SCOPE = 'static-native-disabled-button-initial-state'
VIEWPORT = {'width': 1280, 'height': 900}
STEPS = ('initial', 'tab', 'hover', 'pressed', 'released')
DOCUMENT_URL = 'https://inactive-control-fixture.invalid/source.html'
POLICY = ("default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; "
          "sandbox allow-same-origin allow-scripts")
SELECTOR = re.compile(r'#[a-zA-Z][\w-]*', re.ASCII)
TAGS = {
    'html', 'head', 'meta', 'title', 'style', 'body', 'main', 'section', 'article',
    'header', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'button', 'br',
}
ATTRIBUTES = {'id', 'class', 'style', 'lang', 'dir', 'type', 'disabled', 'charset', 'name', 'content'}

INSTRUMENT = r"""() => {
    window.__inactiveProof = {events: [], blocked: []};
    const events = window.__inactiveProof.events;
    for (const type of ['pointerdown', 'pointerup', 'click', 'keydown', 'focusin', 'input', 'change']) {
        document.addEventListener(type, event => {
            events.push({type, trusted: event.isTrusted, target: event.target.id || '',
                key: event.key || null, pointer: event.pointerType || null});
        }, true);
    }
    document.addEventListener('securitypolicyviolation', event => {
        window.__inactiveProof.blocked.push(event.violatedDirective);
    });
}"""

OBSERVE = r"""(button, [selector, tags, attributes]) => {
    const visible = node => node.checkVisibility({visibilityProperty: true, opacityProperty: true,
        contentVisibilityAuto: true});
    const nodes = [...document.querySelectorAll('*')];
    if (nodes.length > 160) return null;
    const r = button.getBoundingClientRect();
    const frame = [innerWidth, innerHeight];
    const fullyInView = r.width > 0 && r.height > 0 && r.left >= 0 && r.top >= 0 &&
        r.right <= innerWidth && r.bottom <= innerHeight;
    const unsupported = [];
    const overlaps = rect => rect.left < r.right && rect.right > r.left &&
        rect.top < r.bottom && rect.bottom > r.top;
    for (const node of nodes) {
        if (!tags.includes(node.localName) || node.namespaceURI !== 'http://www.w3.org/1999/xhtml' ||
            [...node.attributes].some(attr => !attributes.includes(attr.name))) {
            unsupported.push('markup');
            continue;
        }
        if (!visible(node)) continue;
        const style = getComputedStyle(node);
        if (['box-shadow', 'text-shadow', 'transform', 'clip-path', 'mask-image', 'filter', 'backdrop-filter',
            'translate', 'rotate', 'scale', 'border-image-source', '-webkit-box-reflect']
                .some(name => style.getPropertyValue(name) !== 'none') ||
            style.opacity !== '1' || style.clip !== 'auto' || style.mixBlendMode !== 'normal' ||
            style.outlineStyle !== 'none' ||
            ['::before', '::after'].some(pseudo => {
                const paint = getComputedStyle(node, pseudo);
                return paint.content !== 'normal' && paint.content !== 'none' && paint.display !== 'none';
            })) unsupported.push('paint');
        if (node !== button && !node.contains(button) && [...node.getClientRects()].some(overlaps)) {
            unsupported.push('overlap');
        }
    }
    for (let ancestor = button.parentElement; ancestor; ancestor = ancestor.parentElement) {
        const style = getComputedStyle(ancestor);
        if (style.overflowX !== 'visible' || style.overflowY !== 'visible') unsupported.push('clipping');
    }
    const point = [r.left + r.width / 2, r.top + r.height / 2];
    return {
        stableTarget: button.isConnected && button.ownerDocument === document &&
            document.querySelectorAll(selector).length === 1 && document.querySelector(selector) === button,
        nativeButton: button instanceof HTMLButtonElement && button.parentElement && button.childElementCount === 0 &&
            button.textContent.trim().length > 0 && document.querySelectorAll('button').length === 1 && !button.form,
        nativeDisabled: button.hasAttribute('disabled') && button.disabled && button.matches(':disabled'),
        viewport: frame, displayed: visible(button) && fullyInView, point,
        hitTested: fullyInView && [[0.5, 0.5], [0.25, 0.25], [0.75, 0.25], [0.25, 0.75], [0.75, 0.75]]
            .every(([x, y]) => document.elementFromPoint(r.left + r.width * x, r.top + r.height * y) === button),
        focused: document.activeElement === button,
        documentId: performance.timeOrigin,
        url: location.href,
        unsupported: [...new Set(unsupported)],
        policyViolations: window.__inactiveProof.blocked.slice(),
        animated: document.getAnimations().length > 0,
        html: document.documentElement.outerHTML,
        styles: nodes.map(node => {
            const style = getComputedStyle(node);
            const bounds = node.getBoundingClientRect();
            return [[bounds.x, bounds.y, bounds.width, bounds.height],
                Array.from(style, name => style.getPropertyValue(name))];
        }),
    };
}"""


class Hold(ValueError):
    """Evidence is outside the conditions of this probe."""


class StaticFixture(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag not in TAGS or any(name not in ATTRIBUTES for name, _ in attrs):
            raise Hold('unsupported_authored_markup')


def read_static(raw):
    if len(raw) > 256 * 1024:
        raise Hold('fixture_too_large')
    try:
        parser = StaticFixture()
        parser.feed(raw.decode('utf-8-sig'))
        parser.close()
    except UnicodeDecodeError as error:
        raise Hold('requires_utf8_html') from error


def ax_button(session, selector):
    document = session.send('DOM.getDocument', {'depth': 0})['root']['nodeId']
    node = session.send('DOM.querySelector', {'nodeId': document, 'selector': selector})
    backend = session.send('DOM.describeNode', node)['node']['backendNodeId']
    tree = session.send('Accessibility.getPartialAXTree', {
        'backendNodeId': backend, 'fetchRelatives': False,
    })
    nodes = [node for node in tree['nodes'] if node.get('backendDOMNodeId') == backend and not node.get('ignored')]
    if len(nodes) != 1:
        raise Hold('accessibility_target_not_unique')
    item = nodes[0]
    return {'node': backend, 'role': item.get('role', {}).get('value'),
            'disabled': any(prop.get('name') == 'disabled' and prop.get('value', {}).get('value') is True
                            for prop in item.get('properties', []))}


def snapshot(button, selector):
    state = button.evaluate(OBSERVE, [selector, sorted(TAGS), sorted(ATTRIBUTES)])
    if not state or not state['stableTarget'] or state['url'] != DOCUMENT_URL:
        raise Hold('target_or_document_changed')
    if not state['nativeButton'] or not state['nativeDisabled']:
        raise Hold('native_disabled_button_unconfirmed')
    if not state['displayed'] or not state['hitTested'] or state['unsupported']:
        raise Hold('control_visibility_or_hit_test_unconfirmed')
    if state['focused'] or state['animated'] or state['policyViolations']:
        raise Hold('control_state_or_resource_changed')
    stable = {key: value for key, value in state.items() if key not in {'html', 'styles'}}
    stable['render_state_sha256'] = sha256(json.dumps([state['html'], state['styles']]).encode()).hexdigest()
    return stable


def observe(page, selector):
    locator = page.locator(selector)
    if locator.count() != 1:
        raise Hold('target_not_unique')
    button = locator.element_handle()
    session = page.context.new_cdp_session(page)
    before = snapshot(button, selector)
    accessibility = ax_button(session, selector)
    if accessibility['role'] != 'button' or not accessibility['disabled']:
        raise Hold('native_accessibility_disabled_unconfirmed')

    # Tab is sent while the document initially owns focus. Mouse input then
    # checks the rendered target at its actual center, bypassing locator.click's
    # actionability refusal for disabled controls.
    page.keyboard.press('Tab')
    after_tab = snapshot(button, selector)
    page.mouse.move(*before['point'])
    after_hover = snapshot(button, selector)
    page.mouse.down()
    while_pressed = snapshot(button, selector)
    page.mouse.up()
    after_click = snapshot(button, selector)
    states = dict(zip(STEPS, (before, after_tab, after_hover, while_pressed, after_click), strict=True))
    if any(state != before for state in states.values()):
        raise Hold('interaction_changed_fixture')
    if ax_button(session, selector) != accessibility:
        raise Hold('accessibility_state_changed')
    events = page.evaluate('window.__inactiveProof.events')
    if not confirms_attempts(events, selector):
        raise Hold('trusted_attempts_without_activation_unconfirmed')
    return {'dom': before, 'accessibility': accessibility, 'events': events,
            'step_state_hashes': {name: state['render_state_sha256'] for name, state in states.items()}}


def confirms_attempts(events, selector):
    if (not isinstance(events, list) or len(events) != 3
            or not all(isinstance(event, dict) and event.get('trusted') is True for event in events)):
        return False
    tab, down, up = events
    return (
        tab.get('type') == 'keydown' and tab.get('key') == 'Tab'
        and isinstance(tab.get('target'), str) and tab['target'] != selector[1:]
        and down.get('type') == 'pointerdown' and up.get('type') == 'pointerup'
        and all(event.get('target') == selector[1:] and event.get('pointer') == 'mouse' for event in (down, up))
    )

def probe(source, selector):
    """Return scope-bound evidence without making a page-wide eligibility judgment."""
    from playwright.sync_api import Error as BrowserError, sync_playwright

    if not isinstance(selector, str) or not SELECTOR.fullmatch(selector):
        raise ValueError('測定対象を単一のIDセレクターで指定する')
    source = Path(source)
    raw = source.read_bytes()
    result = {'source': source.name, 'source_sha256': sha256(raw).hexdigest(), 'target': selector,
              'scope': SCOPE, 'status': 'hold', 'blocked_requests': []}
    try:
        read_static(raw)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=shutil.which('chromium'))
            result['browser'] = browser.version
            try:
                context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1,
                                              locale='ja-JP', service_workers='block', accept_downloads=False)
                page = context.new_page()
                served = False

                def route_fixture(route):
                    nonlocal served
                    request = route.request
                    if (not served and request.url == DOCUMENT_URL and request.method == 'GET'
                            and request.is_navigation_request() and request.frame == page.main_frame):
                        served = True
                        route.fulfill(status=200, headers={'content-type': 'text/html; charset=utf-8',
                                                           'content-security-policy': POLICY}, body=raw)
                    else:
                        result['blocked_requests'].append(request.resource_type)
                        route.abort()

                context.route('**/*', route_fixture)
                context.route_web_socket('**/*', lambda socket: socket.close())
                page.add_init_script(f'({INSTRUMENT})()')
                page.goto(DOCUMENT_URL, wait_until='load', timeout=5000)
                result.update(observe(page, selector))
                if result['blocked_requests']:
                    raise Hold('resource_request_blocked')
                result['status'] = 'inactive_observed'
            finally:
                browser.close()
    except Hold as error:
        result['reason'] = str(error)
    except BrowserError:
        result['reason'] = 'chromium_evidence_unavailable'
    return result


def target(criterion, checkpoints, states):
    configured = [state for state in states if 'inactive_control_target' in state]
    if not configured:
        return None
    if (criterion != '1.4.3' or CHECKPOINT not in checkpoints or len(configured) != 1
            or configured[0]['id'] != 'initial'):
        raise ValueError('無効な操作部品の測定は1.4.3-01の初期状態に指定する')
    selector = configured[0]['inactive_control_target']
    if not isinstance(selector, str) or not SELECTOR.fullmatch(selector):
        raise ValueError('無効な操作部品には単一のIDセレクターを指定する')
    return selector


def binding(meta, job, page, selector, source_digest):
    return dict(run_id=meta['run_id'], job_id=job['id'], mode=job['mode'], page=page, url=job['urls'][page],
                state='initial', checkpoint=CHECKPOINT, target=selector, source_sha256=source_digest)


def collect(run, meta, job, page, attempt):
    from . import core

    selector = target(job['criterion'], job['checkpoints'], job['states'])
    if selector is None:
        return
    source = core.local(run/'worker/public'/job['criterion'], page)
    frozen = core.load(run/'integrity.json')['files']
    source_digest = core.file_hash(source)
    if frozen.get(source.relative_to(run.resolve()).as_posix()) != source_digest:
        raise ValueError('無効な操作部品を測定する公開ページが変更された')
    observation = probe(source, selector)
    if observation['source_sha256'] != source_digest:
        raise ValueError('無効な操作部品の測定中に公開ページが変更された')
    core.save(attempt/'inactive-control.json', dict(binding(meta, job, page, selector, source_digest),
                                                    observation=observation))


def confirms_inactivity(proof, selector, source, source_digest):
    if (not isinstance(proof, dict) or proof.get('scope') != SCOPE or proof.get('status') != 'inactive_observed'
            or proof.get('source') != source or proof.get('source_sha256') != source_digest
            or proof.get('target') != selector or proof.get('blocked_requests') != []
            or not isinstance(proof.get('browser'), str) or not proof['browser']
            or not confirms_attempts(proof.get('events'), selector)):
        return False
    dom = proof.get('dom')
    ax = proof.get('accessibility')
    hashes = proof.get('step_state_hashes')
    if not all(isinstance(receipt, dict) for receipt in (dom, ax, hashes)):
        return False
    fingerprint = dom.get('render_state_sha256')
    point = dom.get('point')
    document_id = dom.get('documentId')
    return (
        all(dom.get(key) is True for key in ('stableTarget', 'nativeButton', 'nativeDisabled', 'displayed', 'hitTested'))
        and dom.get('focused') is False and dom.get('animated') is False
        and dom.get('unsupported') == [] and dom.get('policyViolations') == []
        and dom.get('url') == DOCUMENT_URL and dom.get('viewport') == list(VIEWPORT.values())
        and type(document_id) in (int, float) and 0 < document_id < 2**53
        and isinstance(point, list) and len(point) == 2
        and all(type(value) in (int, float) and 0 <= value < limit
                for value, limit in zip(point, VIEWPORT.values(), strict=True))
        and type(ax.get('node')) is int and ax['node'] > 0 and ax.get('role') == 'button' and ax.get('disabled') is True
        and isinstance(fingerprint, str) and re.fullmatch(r'[0-9a-f]{64}', fingerprint) is not None
        and set(hashes) == set(STEPS) and all(digest == fingerprint for digest in hashes.values())
    )


def predictions(run, meta, job, progress, frozen, axe):
    from . import core

    selector = target(job['criterion'], job['checkpoints'], job['states'])
    if selector is None:
        return {}
    result = {}
    for page in job['pages']:
        try:
            attempt, job_receipt = core.completed_attempt(run, job, progress, page, frozen)
            if attempt is None:
                continue
            source = core.local(run/'worker/public'/job['criterion'], page)
            source_digest = frozen.get(source.relative_to(run).as_posix())
            receipt_path = attempt.parent/'inactive-control.json'
            receipt = core.read_frozen(run, receipt_path, frozen)
        except (KeyError, TypeError, ValueError):
            continue
        if (not source_digest or not receipt or any(receipt.get(key) != value
                for key, value in binding(meta, job, page, selector, source_digest).items())):
            continue
        evidence = [path.relative_to(run).as_posix() for path in (job_receipt, receipt_path)]
        observation = receipt.get('observation')
        row = dict(page=page, state='initial', target=selector, checkpoint=CHECKPOINT, outcome='cant_tell',
                   method='program', source='isolated Chromium / native button inactivity', evidence=evidence,
                   observed='表示された無効なネイティブボタンの実入力証拠を確定できない。')
        key = core.observation_key(row)
        previous = axe.get(key)
        if confirms_inactivity(observation, selector, source.name, source_digest):
            if previous and (previous['outcome'] in {'passed', 'failed'} or previous.get('conflicting')):
                row.update(observed='初期表示の無効状態の測定と文字コントラストの判定が矛盾している。',
                           evidence=list(dict.fromkeys(evidence + previous['evidence'])))
            else:
                row.update(outcome='inapplicable',
                           observed='スクリプトのない初期表示で、可視のネイティブボタンの無効状態と、'
                                    '実Tab・ポインター操作で発火又は状態変化がないことを確認した。')
        elif previous:
            continue
        result[key] = row
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True, type=Path, help='self-contained static UTF-8 fixture')
    parser.add_argument('--target', required=True, help='ID selector of the disabled native button')
    args = parser.parse_args()
    if not args.html.is_file() or args.html.suffix.lower() not in {'.html', '.htm'}:
        parser.error('--html must name an existing local HTML file')
    if not SELECTOR.fullmatch(args.target):
        parser.error('--target must name a single ID selector')
    print(json.dumps(probe(args.html, args.target), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
