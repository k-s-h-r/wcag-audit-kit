"""Measure a specified plain text target in a self-contained static benchmark fixture."""
import argparse
import asyncio
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import sys

import PIL  # Check the optional measurement dependency when loading the probe.
from playwright.async_api import Error as BrowserError, async_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/wcag-audit-kit/scripts'))
from text_paint import CAPTURE_STAGES, Held, LOAD_OBSERVER, RGB, capture
from text_paint import analyze_frames as _analyze_frames


DOCUMENT_URL = 'https://text-paint-fixture.invalid/source.html'
RESULT_SCOPE = '1.4.3-02 text-paint measurement on the specified static fixture'
POLICY = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; sandbox allow-same-origin"
VIEWPORT = {'width': 1280, 'height': 900}
ALLOWED_ELEMENTS = {
    'html', 'head', 'meta', 'title', 'style', 'body', 'main', 'section', 'article', 'header', 'footer',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'label', 'strong', 'em', 'b', 'i', 'br',
}


class StaticFixture(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_ELEMENTS or any(name.startswith('on') or name == 'http-equiv' for name, _ in attrs):
            raise Held('requires_self_contained_static_text_html')


def analyze_frames(images, first):
    return _analyze_frames(images, first, VIEWPORT.values())


def probe(source, selector, output, max_images):
    return asyncio.run(_probe(source, selector, output, max_images))


async def _probe(source, selector, output, max_images):
    raw = source.read_bytes()
    result = {
        'source': source.name, 'source_sha256': sha256(raw).hexdigest(), 'target': selector, 'frames': {},
        'image_limit': max_images, 'blocked_requests': [],
        'scope': RESULT_SCOPE,
    }
    output.mkdir(exist_ok=False)
    try:
        if max_images < len(CAPTURE_STAGES):
            raise Held('image_budget_below_seven')
        try:
            validator = StaticFixture()
            validator.feed(raw.decode('utf-8-sig'))
            validator.close()
        except UnicodeDecodeError as error:
            raise Held('requires_utf8_html') from error
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(executable_path=shutil.which('chromium'), args=[
                '--disable-background-networking', '--disable-component-update', '--force-color-profile=srgb',
            ])
            result['browser'] = browser.version
            context = await browser.new_context(viewport=VIEWPORT, device_scale_factor=1, locale='ja-JP', service_workers='block',
                                          accept_downloads=False)
            page = await context.new_page()
            served = False
            blocked = []

            async def route_fixture(route):
                nonlocal served
                request = route.request
                if (not served and request.url == DOCUMENT_URL and request.method == 'GET'
                        and request.is_navigation_request() and request.frame == page.main_frame):
                    served = True
                    await route.fulfill(status=200, headers={
                        'content-type': 'text/html; charset=utf-8',
                        'content-security-policy': POLICY,
                    }, body=raw)
                else:
                    blocked.append(request.resource_type)
                    await route.abort()

            await context.route('**/*', route_fixture)
            await context.route_web_socket('**/*', lambda websocket: websocket.close())
            await page.add_init_script(f'({LOAD_OBSERVER})()')
            try:
                await page.goto(DOCUMENT_URL, wait_until='load', timeout=5000)
                measurement = await capture(page, selector, output, result, interrupted=lambda: bool(blocked))
                if blocked:
                    raise Held('resource_request_blocked')
                result.update(measurement)
            finally:
                result['blocked_requests'] = blocked
                await browser.close()
    except Held as error:
        result.update(status='hold', reason=str(error))
    except BrowserError:
        result.update(status='hold', reason='chromium_session_or_target_unavailable')
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True, type=Path, help='self-contained static UTF-8 fixture')
    parser.add_argument('--target', required=True, help='selector matching one direct text element')
    parser.add_argument('--out', required=True, type=Path, help='new evidence directory')
    parser.add_argument('--max-images', type=int, default=len(CAPTURE_STAGES))
    args = parser.parse_args()
    if not args.html.is_file() or args.html.suffix.lower() not in {'.html', '.htm'}:
        parser.error('--html must name an existing local HTML file')
    if args.out.exists() or not args.out.parent.is_dir():
        parser.error('--out must name a new directory with an existing parent')
    if not args.target.strip() or args.max_images < 0:
        parser.error('--target must not be empty and --max-images must be nonnegative')
    print(json.dumps(probe(args.html, args.target, args.out, args.max_images), ensure_ascii=False, indent=2))
