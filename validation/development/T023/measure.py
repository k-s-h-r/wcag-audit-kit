"""Compare the prototype and original with the same six key inputs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright


def measure(origin, evidence, original):
    evidence.mkdir(parents=True, exist_ok=False)
    digest = sha256(original.read_bytes()).hexdigest()
    result = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True)
        for variant in ('before', 'after'):
            page = browser.new_page(viewport={'width': 1280, 'height': 900}, locale='ja-JP')
            page.goto(f'{origin}/{variant}/')
            trace = []
            for index, key in enumerate(('Tab', 'Enter', 'Tab', 'Enter', 'Tab', 'Enter'), 1):
                page.keyboard.press(key)
                if index == 2:
                    page.wait_for_url('**/visit.html')
                elif index == 6:
                    if variant == 'after':
                        page.wait_for_url(re.compile(r'/confirmation\.html\?people=2$'))
                    else:
                        page.get_by_text('2名以上を選んでから予約内容をご確認ください。').wait_for()
                trace.append(dict(key=key, url=page.url, focus=page.evaluate('document.activeElement?.id'),
                                  shown=page.locator('main').inner_text()))
                if index == 5:
                    snapshot = page.locator('main').aria_snapshot()
                    (evidence / f'{variant}-review-name.txt').write_text(snapshot + '\n')
            page.screenshot(path=evidence / f'{variant}.png')
            result[variant] = dict(trace=trace, confirmed='入力内容を確認しました。' in trace[-1]['shown'],
                                   browser=browser.version, review_ax_snapshot=snapshot)
            page.context.close()
        browser.close()
    assert not result['before']['confirmed'] and result['after']['confirmed'], result
    assert 'button "詳細を見る"' in result['before']['review_ax_snapshot']
    assert 'button "予約内容を確認する"' in result['after']['review_ax_snapshot']
    assert sha256(original.read_bytes()).hexdigest() == digest
    result['original_observations_sha256'] = digest
    (evidence / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('6 inputs for each version: before blocked, after confirmed; AX name aligned')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--original', required=True, type=Path)
    args = parser.parse_args()
    measure(args.origin, args.out, args.original)
