"""Scope keyboard observations to one declared, same-origin child iframe."""
from urllib.parse import urldefrag

from browser_capture import FOCUS, in_scope, normalize


def document_url(url):
    return urldefrag(normalize(url))[0]


def validate(check, config):
    declaration = check.get('frame')
    if 'frame' in check:
        if not isinstance(declaration, dict) or set(declaration) != {'selector', 'url'}:
            raise ValueError('frameはiframeのselectorとurlを指定する')
        selector = declaration['selector']
        url = declaration['url']
        if not isinstance(selector, str) or not selector.strip():
            raise ValueError('frame.selectorは空でないセレクターを指定する')
        if not isinstance(url, str) or not url or urldefrag(url)[1] or not in_scope(url, config):
            raise ValueError('frame.urlは同一オリジンの対象範囲内にあるフラグメントなしの絶対URLを指定する')
    for step in check['steps']:
        for key in ('frame', 'input_frame'):
            if key in step and (not declaration or step[key] != declaration['selector']):
                raise ValueError('手順のframeとinput_frameは宣言したiframeのセレクターを指定する')


class FrameScope:
    def __init__(self, page, declaration):
        self.page = page
        self.declaration = declaration
        self.selector = declaration['selector'] if declaration else None
        self.url = document_url(declaration['url']) if declaration else None

    async def allows_navigation(self, request):
        if not self.declaration or document_url(request.url) != self.url:
            return False
        frame = request.frame
        if frame.parent_frame != self.page.main_frame:
            return False
        # URL alone does not authorize another iframe, even on the same page.
        # Match the browser's actual frame owner in the parent document.
        owner = await frame.frame_element()
        try:
            return await owner.evaluate('''(element, selector) => {
                const root = element.getRootNode();
                if (root !== element.ownerDocument) return false;
                const matches = root.querySelectorAll(selector);
                return element.localName === 'iframe' && matches.length === 1 && matches[0] === element;
            }''', self.selector)
        finally:
            await owner.dispose()

    async def resolve(self, required=False):
        if not self.declaration:
            return None
        from playwright.async_api import Error as BrowserError

        selector = self.selector
        handles = await self.page.query_selector_all('css=' + selector)
        try:
            if not handles and not required:
                return None
            if len(handles) != 1:
                raise ValueError('指定したiframeを一つに絞れない: ' + selector)
            owner = handles[0]
            direct = await owner.evaluate('''element => element.localName === 'iframe'
                && element.getRootNode() === element.ownerDocument''')
            if not direct:
                raise ValueError('直接埋め込まれたiframeを指定する: ' + selector)
            frame = await owner.content_frame()
            if frame is None or frame.parent_frame != self.page.main_frame:
                raise ValueError('指定したiframeの文書を確認できない: ' + selector)
            # Enter can insert a frame before the declared document commits.
            # Do not use the temporary about:blank document for measurements.
            if document_url(frame.url) != self.url:
                await frame.wait_for_url(lambda url: document_url(url) == self.url,
                                         wait_until='domcontentloaded', timeout=2200)
            await frame.wait_for_load_state('domcontentloaded', timeout=2200)
            if (document_url(frame.url) != self.url
                    or not await owner.evaluate('element => element.contentDocument !== null')):
                raise ValueError('iframeの同一オリジンの宣言文書を確認できない: ' + selector)
            return frame
        except BrowserError as exc:
            raise ValueError('指定したiframeの読み込みを確認できない: ' + selector) from exc
        finally:
            for owner in handles:
                await owner.dispose()

    async def focus(self, frame):
        parent = await self.page.evaluate(FOCUS, True)
        if not parent or not parent['documentHasFocus']:
            return self.page.main_frame, parent
        focused = False
        if frame is not None:
            owner = await frame.frame_element()
            try:
                focused = await owner.evaluate('element => element.ownerDocument.activeElement === element')
            finally:
                await owner.dispose()
        if not focused:
            if parent['tag'] in {'iframe', 'frame'}:
                raise ValueError('宣言したiframe以外の文書へフォーカスが入った')
            return self.page.main_frame, parent
        inner = await frame.evaluate(FOCUS, True)
        if not inner or not inner['documentHasFocus'] or inner['tag'] in {'iframe', 'frame'}:
            raise ValueError('指定したiframeの実フォーカスを確認できない: ' + self.selector)
        return frame, dict(inner, frame=self.selector, frameUrl=frame.url)
