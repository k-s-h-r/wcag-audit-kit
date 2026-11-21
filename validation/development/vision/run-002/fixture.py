from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from html import escape

routes = {
    'n2k': {'form': 'schedule', 'confirm': 'preview', 'button': 'invite-more', 'bad': True},
    'j6w': {'form': 'select', 'confirm': 'verify', 'button': 'add-companion', 'bad': False},
}

def document(content):
    return ('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>工房の見学枠</title><style>body{font:18px sans-serif;margin:2rem;color:#212a34}'
            'button{font:inherit;margin:.6rem .8rem .4rem 0;padding:.35rem .55rem}'
            ':focus-visible{outline:3px solid #2447ad;outline-offset:2px}</style>'
            f'<main>{content}</main></html>').encode()

def page(path):
    parts = path.strip('/').split('/')
    key = parts[0]
    variant = routes.get(key)
    if variant is None:
        return None
    start = f'/{key}/'
    step = start + variant['form']
    confirm = start + variant['confirm']
    if len(parts) == 1:
        return document(f'<h1>工房の見学枠</h1><p>見学は12月13日に開催します。</p><a href="{step}">見学枠を選ぶ</a>')
    if parts[1] == variant['confirm']:
        return document('<h1>見学枠の確認</h1><p>12月13日。見学人数 2 名。</p>')
    if parts[1] != variant['form']:
        return None
    label = ' aria-label="詳しい情報"' if variant['bad'] else ''
    press = 'pointerup' if variant['bad'] else 'click'
    button = variant['button']
    return document(f'''
      <h1>12月13日の見学枠</h1>
      <p>お連れの方も含め、2名で参加できます。</p>
      <p>見学人数 <output id="attendees">1</output> 名</p>
      <button id="{button}" type="button">同伴者を追加する</button>
      <button id="review-slot"{label} type="button">確認画面に進む</button>
      <p id="advice"></p>
      <script>
      const count = document.getElementById('attendees');
      document.getElementById('{button}').addEventListener('{press}', () => count.value = '2');
      document.getElementById('review-slot').addEventListener('click', () => {{
        if (count.value === '2') location.href = '{confirm}?attendees=2';
        else document.getElementById('advice').textContent = '見学人数を2名にしてください。';
      }});
      </script>''')

class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        location = urlsplit(self.path)
        data = page(location.path)
        if data is None or (location.path.endswith(('/preview', '/verify'))
                            and parse_qs(location.query) != {'attendees': ['2']}):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('content-type', 'text/html; charset=utf-8')
        self.send_header('content-length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 43922), Fixture).serve_forever()
