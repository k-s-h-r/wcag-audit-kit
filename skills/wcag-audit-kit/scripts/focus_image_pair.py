"""Collect viewport images around a verified keyboard focus change."""
from pathlib import Path
import struct

from browser_capture import OPEN_FOCUS_PATH


SNAPSHOT = r"""
(element, previous) => {
    const doc = element.ownerDocument;
    const connected = element.isConnected && doc === document && window === window.top;
    const active = (""" + OPEN_FOCUS_PATH + r""")(doc).element;
    const rect = element.getBoundingClientRect().toJSON();
    const visual = window.visualViewport;
    const viewport = {
        width: window.innerWidth, height: window.innerHeight, dpr: window.devicePixelRatio,
        visual: visual && {
            width: visual.width, height: visual.height, scale: visual.scale,
            offset_x: visual.offsetLeft, offset_y: visual.offsetTop,
        },
    };
    const {left, top, right, bottom, width, height} = rect;
    return {
        connected, same_target: previous === null || previous === element,
        url: location.href, time_origin: performance.timeOrigin,
        rect: {left, top, right, bottom, width, height},
        viewport, scroll: {x: window.scrollX, y: window.scrollY},
        document_focused: doc.hasFocus(), focused: active === element,
        focus_visible: element.matches(':focus-visible'),
        in_viewport: width > 0 && height > 0 && visual !== null
            && left < visual.offsetLeft + visual.width && right > visual.offsetLeft
            && top < visual.offsetTop + visual.height && bottom > visual.offsetTop,
    };
}
"""

GEOMETRY = ('viewport', 'scroll', 'rect')
FRAME = ('url', 'time_origin')
FOCUS = ('document_focused', 'focused', 'focus_visible')
REASONS = {
    'not_started': 'キー入力前の画像は未取得です。',
    'screenshots_off': 'この検証モードでは画像を取得しません。',
    'states_only': '現在の画像設定は探索状態の画像だけを取得します。',
    'image_limit': '画像の上限までに前後2枚を取得できません。',
    'unsupported_frame': '主文書以外のフォーカス画像は取得できません。',
    'target_unresolved': '画像を取得する対象を1つに特定できません。',
    'target_changed': 'キー入力後に同じ対象を確認できません。',
    'document_changed': 'キー入力の前後で文書が変わりました。',
    'focus_unconfirmed': '対象にフォーカスが移ったことを確認できません。',
    'capture_state_changed': '画像取得中に対象の位置、表示条件又はフォーカスが変わりました。',
    'target_offscreen': '対象が表示範囲の外にあるため、画像でフォーカス表示を比較できません。',
    'geometry_changed': 'キー入力の前後で表示範囲、スクロール位置又は対象の位置が変わりました。',
    'capture_error': '画像の取得に失敗しました。',
    'awaiting_after': 'キー入力後の画像は未取得です。',
    'interrupted': 'キー入力後の状態を確認できませんでした。',
    'captured': '同じ表示条件で実キー入力前後の画像を取得しました。フォーカスの見え方は画像で確認してください。',
}


def changed(before, after, fields):
    return any(before[field] != after[field] for field in fields)


class FocusImagePair:
    """Capture evidence only. The caller confirms trusted key delivery before after()."""

    def __init__(self, scope, selector, images, dest):
        self.scope = scope
        self.selector = selector
        self.images = images
        self.dest = Path(dest)
        self.receipt = {'selector': selector}
        self.target = None
        self._result('not_run', 'not_started')

    def _result(self, status, code, reason=None):
        self.receipt.update(status=status, reason_code=code, reason=reason or REASONS[code])

    def _capture_error(self, error):
        self.receipt['error'] = str(error)
        status = 'partial' if self.receipt.get('before', {}).get('image') else 'error'
        self._result(status, 'capture_error')

    def invalidate(self, reason=None):
        """Retain collected evidence without pairing it with an unverified route."""
        status = self.receipt['status']
        if status in ('skipped', 'error'):
            return
        if self.receipt.get('after', {}).get('image'):
            self._result('incomparable', 'interrupted', reason)
        elif status == 'not_run' or self.receipt.get('before', {}).get('image'):
            self._result('partial', 'interrupted', reason)

    async def _resolve(self):
        locator = self.scope.locator(self.selector)
        if await locator.count() == 1:
            return await locator.element_handle(timeout=1500)
        return None

    async def _image(self, stage, handle, snapshot):
        path = self.dest / f'focus-{stage}.png'

        async def screenshot():
            pixels = await self.scope.page.screenshot(
                type='png', full_page=False, animations='allow', caret='hide', timeout=3000)
            if pixels[:8] != b'\x89PNG\r\n\x1a\n' or len(pixels) < 24:
                raise ValueError('PNG画像を取得できませんでした。')
            width, height = struct.unpack('>II', pixels[16:24])
            path.write_bytes(pixels)
            snapshot['pixels'] = {'width': width, 'height': height}

        if not await self.images.capture_with(path, 'detail', screenshot):
            raise RuntimeError('画像の上限又は設定が取得前に変わりました。')
        snapshot['image'] = path.relative_to(self.images.run).as_posix()
        later = await handle.evaluate(SNAPSHOT, self.target)
        return later['connected'] and not changed(snapshot, later, FRAME + GEOMETRY + FOCUS)

    async def before(self):
        policy = self.images.policy
        if policy['screenshots'] != 'all':
            code = 'screenshots_off' if policy['screenshots'] == 'off' else 'states_only'
            self._result('skipped', code)
            return
        limit = policy['max_images']
        if limit is not None and self.images.counts.get(self.images.page, 0) + 2 > limit:
            self._result('skipped', 'image_limit')
            return
        if self.scope != self.scope.page.main_frame:
            self._result('not_run', 'unsupported_frame')
            return

        try:
            self.target = await self._resolve()
            if self.target is None:
                self._result('not_run', 'target_unresolved')
                return
            snapshot = await self.target.evaluate(SNAPSHOT, None)
            self.receipt['before'] = snapshot
            if not snapshot['connected'] or not snapshot['document_focused'] or snapshot['focused']:
                self._result('incomparable', 'focus_unconfirmed')
                return
            if await self._image('before', self.target, snapshot):
                self._result('partial', 'awaiting_after')
            else:
                self._result('partial', 'capture_state_changed')
        except Exception as error:
            self._capture_error(error)

    async def after(self):
        if self.receipt['reason_code'] not in ('awaiting_after', 'capture_state_changed'):
            return
        stable_before = self.receipt['reason_code'] == 'awaiting_after'
        before = self.receipt['before']
        current = None
        try:
            current = await self._resolve()
            if current is None:
                self._result('partial', 'target_unresolved')
                return
            after = await current.evaluate(SNAPSHOT, None)
            self.receipt['after'] = after
            after['same_target'] = not changed(before, after, FRAME) and await current.evaluate(
                '(element, previous) => element === previous', self.target)
            if changed(before, after, FRAME):
                self._result('partial', 'document_changed')
            elif not after['connected'] or not after['same_target']:
                self._result('partial', 'target_changed')
            elif not after['document_focused'] or not after['focused']:
                self._result('partial', 'focus_unconfirmed')
            else:
                stable_after = await self._image('after', current, after)
                if not stable_before or not stable_after:
                    self._result('incomparable', 'capture_state_changed')
                elif not before['in_viewport'] or not after['in_viewport']:
                    self._result('incomparable', 'target_offscreen')
                elif changed(before, after, GEOMETRY + ('pixels',)):
                    self._result('incomparable', 'geometry_changed')
                else:
                    self._result('captured', 'captured')
        except Exception as error:
            self._capture_error(error)
        finally:
            if current is not None:
                await self._dispose(current)

    async def close(self):
        if self.target is not None:
            await self._dispose(self.target)
            self.target = None

    @staticmethod
    async def _dispose(handle):
        from playwright.async_api import Error as BrowserError
        try:
            await handle.dispose()
        except BrowserError:
            # The document/context may already have been replaced or closed.
            pass
