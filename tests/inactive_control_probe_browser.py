"""Compare a native disabled control against interactive and ambiguous fixtures."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.inactive_control_probe import probe


def html(body):
    return '<!doctype html><html lang="en"><title>Inactive control comparison</title>' + body + '</html>'


def exercise_counterexample(content):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium'))
        try:
            page = browser.new_page()
            page.set_content(content)
            button = page.locator('#subject')
            assert button.is_disabled()
            bounds = button.bounding_box()
            page.mouse.click(bounds['x'] + bounds['width'] / 2, bounds['y'] + bounds['height'] / 2)
            assert page.locator('#result').inner_text() == 'reacted'
            assert page.evaluate('window.trustedPointer') is True
        finally:
            browser.close()


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'benchmarks/cases/1.4.3/public/p07.html'
    digest = sha256(source.read_bytes()).hexdigest()
    measured = probe(source, '#subject')
    assert measured['status'] == 'inactive_observed', measured
    assert measured['source_sha256'] == digest == sha256(source.read_bytes()).hexdigest()
    assert measured['accessibility']['role'] == 'button' and measured['accessibility']['disabled']
    assert measured['dom']['viewport'] == [1280, 900] and measured['dom']['hitTested']
    assert not measured['blocked_requests']
    assert [event['type'] for event in measured['events']] == ['keydown', 'pointerdown', 'pointerup']
    assert all(event['trusted'] for event in measured['events'])

    button = '<button id="subject" disabled>Save</button>'
    reactive = html(button + '<p id="result">ready</p><script>'
                    "document.addEventListener('pointerdown', event => {"
                    "if (event.target.id !== 'subject') return;"
                    "window.trustedPointer = event.isTrusted;"
                    "document.querySelector('#result').textContent = 'reacted'; });</script>")
    cases = {
        'enabled': (html(button.replace(' disabled', '')), 'native_disabled_button_unconfirmed'),
        'aria-disabled': (html(button.replace(' disabled', ' aria-disabled="true"')), 'unsupported_authored_markup'),
        'delegated-script': (reactive, 'unsupported_authored_markup'),
        'inline-event': (html(button.replace(' disabled', ' disabled onpointerdown="this.textContent=1"')),
                         'unsupported_authored_markup'),
        'linked-label': (html('<label for="other">' + button + '</label>'), 'unsupported_authored_markup'),
        'multiple-controls': (html(button + '<button>Other</button>'), 'native_disabled_button_unconfirmed'),
        'duplicate-target': (html(button + '<span id="subject">Duplicate</span>'), 'target_not_unique'),
        'covered': (html(button + '<div style="position:fixed;inset:0;background:white;pointer-events:none"></div>'),
                    'control_visibility_or_hit_test_unconfirmed'),
        'css-only-state': (html('<style>#result{display:none}button:hover+#result{display:block}</style>'
                                + button + '<p id="result">revealed</p>'), 'interaction_changed_fixture'),
    }
    exercise_counterexample(reactive)
    observations = {'p07': measured, 'reactive_disabled_received_trusted_pointer': True}
    for name, (content, reason) in cases.items():
        fixture = out / (name + '.html')
        fixture.write_text(content)
        observation = probe(fixture, '#subject')
        assert observation['status'] == 'hold' and observation['reason'] == reason, (name, observation)
        observations[name] = observation
    (out / 'observed.json').write_text(json.dumps(observations, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'inactive_observed': ['p07'], 'held': list(cases),
                      'reactive_disabled_received_trusted_pointer': True}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    run(parser.parse_args().out)
