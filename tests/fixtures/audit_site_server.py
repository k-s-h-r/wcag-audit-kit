"""Owned five-page acceptance fixture. Test accounts and data only."""
import argparse
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent/'audit-site'
SESSIONS={}
PAGES={'/':'Home','/profile':'Edit profile','/media':'Video instructions','/help':'Help','/login':'Sign in'}


class Handler(BaseHTTPRequestHandler):
    def session(self):
        cookie=SimpleCookie(self.headers.get('Cookie',''))
        value=cookie.get('audit_demo')
        return SESSIONS.get(value.value) if value else None

    def send(self,status,body,content_type='application/json; charset=utf-8',cookie=None):
        data=json.dumps(body,ensure_ascii=False).encode() if isinstance(body,dict) else body
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(data)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/sitemap.xml':
            body='<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>http://127.0.0.1:'+str(self.server.server_port)+p+'</loc></url>' for p in PAGES)+'</urlset>'
            self.send(200,body.encode(),'application/xml');return
        if path.startswith('/assets/'):
            name=path.removeprefix('/assets/')
            files={'app.css':'text/css','app.js':'text/javascript','clip.webm':'video/webm','captions.vtt':'text/vtt'}
            if name in files:
                self.send(200,(ROOT/name).read_bytes(),files[name]);return
        if path in PAGES:
            content=(ROOT/('home.html' if path=='/' else path[1:]+'.html')).read_text()
            if path=='/profile' and not self.session():
                content='<h1>Sign in to edit your profile</h1><p id="signed-out">Your profile is available after <a href="/login">signing in</a>.</p>'
            nav=''.join('<a href="'+p+'"'+(' aria-current="page"' if path==p else '')+'>'+escape(title)+'</a>' for p,title in PAGES.items())
            account=('<button type="button" id="sign-out">Sign out</button>' if self.session() else '<span id="signed-out-account">Signed out</span>')
            page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>'''+escape(PAGES[path])+''' — Profile demo</title><link rel="stylesheet" href="/assets/app.css"></head><body>
<a class="skip" href="#main">Skip to main content</a><header><p>Profile demo</p><nav aria-label="Main">'''+nav+'''</nav>'''+account+'''</header>
<main id="main" tabindex="-1">'''+content+'''</main><footer><a href="/help">Help</a><p>Contact: example@example.test</p></footer>
<script src="/assets/app.js"></script></body></html>'''
            self.send(200,page.encode(),'text/html; charset=utf-8');return
        self.send(404,{'error':'not found'})

    def do_POST(self):
        path=urlsplit(self.path).path
        length=int(self.headers.get('Content-Length',0))
        if length>10000:self.send(413,{'error':'fixture limit'});return
        body=json.loads(self.rfile.read(length) or '{}')
        if path=='/api/login':
            if body.get('email')!='demo@example.test' or body.get('password')!='Test-password-42!':
                self.send(401,{'error':'Use the demo email and password shown in Help.'});return
            token=secrets.token_hex(16);SESSIONS[token]={'profile':{'name':'Demo User','email':'demo@example.test'}}
            self.send(200,{'signed_in':True},cookie='audit_demo='+token+'; HttpOnly; SameSite=Strict; Path=/');return
        if path=='/api/logout':
            self.send(200,{'signed_in':False},cookie='audit_demo=; Max-Age=0; Path=/');return
        if path=='/api/profile':
            session=self.session()
            if session is None:self.send(401,{'error':'Sign in before saving.'});return
            if not body.get('name','').strip() or '@' not in body.get('email',''):
                self.send(400,{'error':'Enter a name and an email address.'});return
            session['profile']=body
            self.send(200,{'saved':body});return
        self.send(404,{'error':'not found'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=4330)
    args=parser.parse_args();ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
