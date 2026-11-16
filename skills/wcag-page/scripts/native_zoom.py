"""Real Chromium zoom through native X11 key input on a dedicated display."""
import ctypes
import ctypes.util
import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
import select
import shutil
import subprocess
import sys


METRICS = """() => ({innerWidth,innerHeight,outerWidth,outerHeight,devicePixelRatio,
 visualScale:visualViewport?.scale,docWidth:document.documentElement.scrollWidth,
 docHeight:document.documentElement.scrollHeight,bodyZoom:document.body?getComputedStyle(document.body).zoom:null,
 rootZoom:getComputedStyle(document.documentElement).zoom})"""
ZOOM_FACTORS={1,1.1,1.25,1.5,1.75,2,2.5,3,4}


def capabilities():
    return {'backend':'Linux Xvfb/XTest native Chromium zoom',
        'platform_supported':sys.platform=='linux','xvfb':os.environ.get('WCAG_XVFB') or shutil.which('Xvfb'),
        'X11':bool(ctypes.util.find_library('X11')),'XTest':bool(ctypes.util.find_library('Xtst')),
        'runtime_verified':False,'note':'依存物の検出のみ。実際の拡大は実行時に測定して確認する'}


class NativeDisplay:
    """Own only the X server created here; never send keys to an existing desktop."""
    def __init__(self, evidence_dir, width=1600, height=1200):
        self.dest=Path(evidence_dir)
        self.width=width;self.height=height
        self.process=None;self.log=None;self.connection=None

    def start(self):
        executable=os.environ.get('WCAG_XVFB') or shutil.which('Xvfb')
        if not executable:
            raise RuntimeError('実ブラウザー拡大にはLinuxのXvfbとX11/XTestが必要。WCAG_XVFBで専用のXvfbを指定できる')
        if sys.platform!='linux':
            raise RuntimeError('この拡大アダプターはLinuxの専用X11環境用')
        number=next((n for n in (secrets.randbelow(2000)+100 for _ in range(30))
                     if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
        if number is None:raise RuntimeError('専用X displayの空きを確保できない')
        self.display=f':{number}'
        read_fd,write_fd=os.pipe()
        self.log=(self.dest/'native-x11.log').open('w')
        try:
            self.process=subprocess.Popen([executable,self.display,'-displayfd',str(write_fd),
                '-screen','0',f'{self.width}x{self.height}x24','-nolisten','tcp'],
                pass_fds=(write_fd,),stdout=self.log,stderr=self.log)
            os.close(write_fd);write_fd=None
            if not select.select([read_fd],[],[],8)[0]:raise RuntimeError('Xvfbの起動確認がタイムアウトした')
            ready=os.read(read_fd,128).decode().strip()
            if ready!=str(number):raise RuntimeError('専用Xvfbの起動に失敗した。native-x11.logを確認する')
            x11_name=ctypes.util.find_library('X11');xtst_name=ctypes.util.find_library('Xtst')
            if not x11_name or not xtst_name:raise RuntimeError('libX11又はlibXtstが見つからない')
            self.x11=ctypes.CDLL(x11_name);self.xtst=ctypes.CDLL(xtst_name)
            self.x11.XOpenDisplay.argtypes=[ctypes.c_char_p];self.x11.XOpenDisplay.restype=ctypes.c_void_p
            self.x11.XCloseDisplay.argtypes=[ctypes.c_void_p]
            self.connection=self.x11.XOpenDisplay(self.display.encode())
            if not self.connection:raise RuntimeError('専用X displayに接続できない')
            self.x11.XStringToKeysym.argtypes=[ctypes.c_char_p];self.x11.XStringToKeysym.restype=ctypes.c_ulong
            self.x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];self.x11.XKeysymToKeycode.restype=ctypes.c_uint
            self.xtst.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
            self.x11.XSync.argtypes=[ctypes.c_void_p,ctypes.c_int]
            return self
        except Exception:
            self.close();raise
        finally:
            os.close(read_fd)
            if write_fd is not None:os.close(write_fd)

    @property
    def env(self):
        return {**os.environ,'DISPLAY':self.display}

    def key(self,name,down):
        code=self.x11.XKeysymToKeycode(self.connection,self.x11.XStringToKeysym(name.encode()))
        if not code:raise RuntimeError('X11キーが見つからない: '+name)
        if not self.xtst.XTestFakeKeyEvent(self.connection,code,int(down),0):
            raise RuntimeError('ネイティブキー入力に失敗した')
        self.x11.XSync(self.connection,False)

    def shortcut(self,name):
        self.key('Control_L',True)
        try:
            self.key(name,True);self.key(name,False)
        finally:
            self.key('Control_L',False)

    async def screenshot(self,path):
        """Optional desktop proof, including Chromium's own zoom indicator."""
        command=shutil.which('ffmpeg')
        if not command:raise RuntimeError('デスクトップ画像にはffmpegが必要')
        process=await asyncio.create_subprocess_exec(command,'-nostdin','-hide_banner','-loglevel','error',
            '-y','-f','x11grab','-video_size',f'{self.width}x{self.height}','-i',self.display,
            '-frames:v','1','-update','1',str(path),stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=asyncio.subprocess.PIPE)
        try:
            _,error=await asyncio.wait_for(process.communicate(),15)
            if process.returncode:raise RuntimeError(error.decode()[-2000:])
        except BaseException:
            if process.returncode is None:process.kill();await process.wait()
            raise

    def close(self):
        if self.connection:
            self.x11.XCloseDisplay(self.connection);self.connection=None
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        if self.log:self.log.close();self.log=None


def zoom_verified(baseline, measured, factor):
    """Require a browser zoom change while retaining the physical outer width."""
    ratio=measured['devicePixelRatio']/baseline['devicePixelRatio']
    return (abs(ratio-factor)<0.015 and
            abs(measured['innerWidth']*factor-baseline['innerWidth'])<=factor+1 and
            measured['outerWidth']==baseline['outerWidth'] and
            abs(measured['visualScale']-1)<0.01)


async def apply_zoom(page,display,factor,viewport,on_step=None):
    if factor not in ZOOM_FACTORS:raise ValueError('ネイティブ拡大率が未対応')
    await page.bring_to_front()
    session=await page.context.new_cdp_session(page)
    window=await session.send('Browser.getWindowForTarget')
    await session.send('Browser.setWindowBounds',{'windowId':window['windowId'],
        'bounds':{'width':viewport['width'],'height':viewport['height'],'windowState':'normal'}})
    display.shortcut('0');await page.wait_for_timeout(250)
    baseline=await page.evaluate(METRICS)
    # Resize the native window to the requested content size at 100%.
    await session.send('Browser.setWindowBounds',{'windowId':window['windowId'],'bounds':{
        'width':baseline['outerWidth']+viewport['width']-baseline['innerWidth'],
        'height':baseline['outerHeight']+viewport['height']-baseline['innerHeight']}})
    await page.wait_for_timeout(200)
    baseline=await page.evaluate(METRICS)
    if any(abs(baseline['inner'+axis]-viewport[axis.lower()])>1 for axis in ['Width','Height']):
        raise RuntimeError('100%時の実際のコンテンツ表示領域を設定値に合わせられない')
    if on_step:await on_step(100,baseline)
    steps=[]
    def completed(measured):
        return {'mechanism':'native XTest keys into dedicated Chromium window','factor':factor,
            'baseline':baseline,'observed':measured,'steps':steps,
            'verified':True,'observed_at':datetime.now(timezone.utc).isoformat(),
            'note':'実ブラウザー拡大の操作確認。内容・機能の保持又はWCAG合格の判定ではない'}
    if factor==1:return completed(baseline)
    for _ in range(12):
        display.shortcut('equal');await page.wait_for_timeout(180)
        measured=await page.evaluate(METRICS)
        previous=steps[-1]['metrics'] if steps else baseline
        if measured['devicePixelRatio']<=previous['devicePixelRatio']+0.01:
            raise RuntimeError('ネイティブ拡大キーが反映されない。対象ブラウザーの前面・フォーカスを確認する')
        steps.append({'native_keys':['Control_L','equal'],'metrics':measured})
        if on_step:await on_step(round(measured['devicePixelRatio']/baseline['devicePixelRatio']*100),measured)
        if zoom_verified(baseline,measured,factor):
            return completed(measured)
        if measured['devicePixelRatio']/baseline['devicePixelRatio']>factor+0.1:break
    raise RuntimeError('指定した実ブラウザー拡大率を観測できない')
