"""Native Debian Orca in a private D-Bus/X11 session, independent of Guidepup."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from native_zoom import NativeDisplay


def now():
    return datetime.now(timezone.utc).isoformat()


class NativeOrcaRuntime:
    def __init__(self, root, output):
        self.root = Path(root).resolve()
        self.output = Path(output)
        self.display = NativeDisplay(self.output, width=1600, height=1200)
        self.processes = []
        self.handles = []
        self.master = None
        self.slave = None
        self.log = None
        self.env = None
        self.pty_error = None

    async def start(self):
        root = self.root
        work = self.output
        for name in ['usr/bin/orca', 'usr/bin/Xvfb', 'usr/bin/speech-dispatcher']:
            if not (root / name).is_file():
                raise ValueError('Orcaの検証用パッケージがない: ' + str(root / name))
        os.environ['WCAG_XVFB'] = str(root / 'usr/bin/Xvfb')
        self.display.start()
        env = self.display.env
        env.update({'TZ': 'UTC', 'PYTHONPATH': str(root / 'usr/lib/python3/dist-packages'),
            'LD_LIBRARY_PATH': str(root / 'usr/lib/x86_64-linux-gnu'),
            'GI_TYPELIB_PATH': str(root / 'usr/lib/x86_64-linux-gnu/girepository-1.0'),
            'XDG_CACHE_HOME': str(work / 'cache'), 'XDG_CONFIG_HOME': str(work / 'config'),
            'XDG_DATA_HOME': str(work / 'data'), 'GSETTINGS_BACKEND': 'memory',
            'NO_AT_BRIDGE': '0', 'SPEECHD_PLUGIN_DIR': str(root / 'usr/lib/x86_64-linux-gnu/speech-dispatcher'),
            'ESPEAK_DATA_PATH': str(root / 'usr/lib/x86_64-linux-gnu'),
            'SPEECHD_ADDRESS': 'unix_socket:' + str(work / 'speechd.sock')})
        self.env = env
        for name in ['cache', 'config', 'data', 'prefs', 'logs', 'speech-config/modules']:
            (work / name).mkdir(parents=True, exist_ok=True)
        (work / 'speech-config/speechd.conf').write_text(
            f'LogLevel 5\nLogDir "{work / "logs"}"\nDefaultModule espeak-ng\n'
            'AddModule "espeak-ng" "sd_espeak-ng" "espeak-ng.conf"\n'
            'AudioOutputMethod "alsa"\nAudioALSADevice "null"\n')
        (work / 'speech-config/modules/espeak-ng.conf').write_bytes(
            (root / 'etc/speech-dispatcher/modules/espeak-ng.conf').read_bytes())
        subprocess.run(['dbus-update-activation-environment', 'DISPLAY', 'XDG_CACHE_HOME',
                        'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'GSETTINGS_BACKEND'], env=env, check=True)
        self.launch([str(root / 'usr/bin/speech-dispatcher'), '-s', '-t', '0', '-c', 'unix_socket',
            '-S', str(work / 'speechd.sock'), '-P', str(work / 'speechd.pid'), '-C', str(work / 'speech-config'),
            '-m', str(root / 'usr/lib/speech-dispatcher-modules'), '-L', str(work / 'logs')], 'speechd')
        for _ in range(40):
            if (work / 'speechd.sock').exists():
                break
            await asyncio.sleep(.1)
        if not (work / 'speechd.sock').exists():
            raise ValueError('Speech Dispatcherのソケットを作成できない')
        # A private PTY makes Orca's debug file line-buffered without patching Orca.
        # Preserve the entire stream, and still index phrases by their own timestamps.
        import pty
        self.master, self.slave = pty.openpty()
        os.set_blocking(self.master, False)
        self.log = (work / 'orca-debug.log').open('wb', buffering=0)
        asyncio.get_running_loop().add_reader(self.master, self.drain)
        # Orca's --replace terminates every Orca process owned by this account,
        # including instances outside this private display and D-Bus session.
        reader = self.launch([str(root / 'usr/bin/orca'), '--debug-file',
            os.ttyname(self.slave), '--user-prefs', str(work / 'prefs'), '--enable', 'speech',
            '--disable', 'braille'], 'orca')
        await asyncio.sleep(3)
        if reader.poll() is not None:
            raise ValueError('Orcaが起動後に終了した。別のOrcaが起動していると検証を中断する。詳細はorca.stdoutを確認してください。')
        package_path = root / 'package-manifest.json'
        packages = json.loads(package_path.read_text()) if package_path.exists() else {}
        if packages:
            (work / 'package-manifest.json').write_bytes(package_path.read_bytes())
        version_line = re.search(r'DEBUGGING TOOLS MANAGER: Orca version ([^,\r\n]+)', self.log_text())
        if not version_line:
            raise ValueError('起動したOrcaのログから版を確認できない')
        version = version_line.group(1)
        return {'reader': 'Orca', 'reader_version': version,
                'debian_package': packages.get('orca', {}).get('Version'),
                'backend': 'native Debian Orca / AT-SPI; independent of Guidepup',
                'audio_output': 'ALSA null; speech transcript, no acoustic recording',
                'debug_capture': 'private PTY, unmodified Orca; UTC timestamps',
                'installation_verified': True, 'simulation': False}

    def launch(self, command, name):
        handle = (self.output / (name + '.stdout')).open('w')
        self.handles.append(handle)
        process = subprocess.Popen(command, env=self.env, stdout=handle, stderr=subprocess.STDOUT)
        self.processes.append(process)
        return process

    def drain(self):
        try:
            while self.master is not None:
                data = os.read(self.master, 65536)
                if not data:
                    return
                self.log.write(data)
        except BlockingIOError:
            pass
        except OSError as error:
            # An EOF after the writer closes is expected; retain any other error.
            if error.errno != 5:
                self.pty_error = str(error)

    def press(self, keys):
        down = []
        try:
            for key in keys:
                self.display.key(key, True)
                down.append(key)
        finally:
            for key in reversed(down):
                self.display.key(key, False)

    def log_text(self):
        self.drain()
        path = self.output / 'orca-debug.log'
        return path.read_text(errors='replace') if path.exists() else ''

    async def close(self):
        for process in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
                try:
                    await asyncio.to_thread(process.wait, timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    await asyncio.to_thread(process.wait)
        if self.master is not None:
            self.drain()
            asyncio.get_running_loop().remove_reader(self.master)
            os.close(self.master)
            self.master = None
        if self.slave is not None:
            os.close(self.slave)
            self.slave = None
        if self.log:
            self.log.close()
        for handle in self.handles:
            handle.close()
        self.display.close()
        path = self.output / 'orca-debug.log'
        return {'debug_log_sha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                'pty_error': self.pty_error}
