"""Diagnostic comparison with native Debian Orca; this does not run Guidepup.

Uses previously extracted packages in --root, without installing OS packages.
Creates its own D-Bus/Xvfb session and writes only a new --out directory.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / 'scripts'))
from native_zoom import NativeDisplay
from orca_log import speech_in_window


def now():
    return datetime.now(timezone.utc).isoformat()


def run(args):
    root = args.root.resolve()
    work = args.out.resolve()
    work.mkdir(parents=True, exist_ok=False)
    os.environ['WCAG_XVFB'] = str(root / 'usr/bin/Xvfb')
    display = NativeDisplay(work, width=1280, height=1000)
    processes = []
    handles = []
    observations = []
    result = {'status': 'blocked', 'started_at': now(), 'observations': observations,
              'backend': 'native Orca debug speech output; NOT Guidepup',
              'audio': 'Speech Dispatcher configured with ALSA null; no acoustic recording',
              'log_timezone': 'UTC', 'wcag_judgement': None}

    def start(command, name, env):
        handle = (work / (name + '.stdout')).open('w')
        handles.append(handle)
        process = subprocess.Popen(command, env=env, stdout=handle, stderr=subprocess.STDOUT)
        processes.append(process)
        return process

    try:
        display.start()
        env = display.env
        env.update({
            'TZ': 'UTC',
            'PYTHONPATH': str(root / 'usr/lib/python3/dist-packages'),
            'LD_LIBRARY_PATH': str(root / 'usr/lib/x86_64-linux-gnu'),
            'GI_TYPELIB_PATH': str(root / 'usr/lib/x86_64-linux-gnu/girepository-1.0'),
            'XDG_CACHE_HOME': str(work / 'cache'), 'XDG_CONFIG_HOME': str(work / 'config'),
            'XDG_DATA_HOME': str(work / 'data'), 'GSETTINGS_BACKEND': 'memory',
            'NO_AT_BRIDGE': '0',
            'SPEECHD_PLUGIN_DIR': str(root / 'usr/lib/x86_64-linux-gnu/speech-dispatcher'),
            'ESPEAK_DATA_PATH': str(root / 'usr/lib/x86_64-linux-gnu'),
            'SPEECHD_ADDRESS': 'unix_socket:' + str(work / 'speechd.sock'),
        })
        for name in ['cache', 'config', 'data', 'logs', 'prefs', 'speech-config/modules']:
            (work / name).mkdir(parents=True, exist_ok=True)
        (work / 'speech-config/speechd.conf').write_text(
            f'LogLevel 5\nLogDir "{work / "logs"}"\nDefaultModule espeak-ng\n'
            'AddModule "espeak-ng" "sd_espeak-ng" "espeak-ng.conf"\n'
            'AudioOutputMethod "alsa"\nAudioALSADevice "null"\n')
        (work / 'speech-config/modules/espeak-ng.conf').write_bytes(
            (root / 'etc/speech-dispatcher/modules/espeak-ng.conf').read_bytes())
        package_bytes = (root / 'package-manifest.json').read_bytes()
        (work / 'package-manifest.json').write_bytes(package_bytes)
        packages = json.loads(package_bytes)
        result['environment'] = {'system': platform.system(), 'kernel': platform.release(),
            'orca_debian_package': packages['orca']['Version'],
            'speech_dispatcher_debian_package': packages['speech-dispatcher']['Version'],
            'package_manifest_sha256': hashlib.sha256(package_bytes).hexdigest()}
        subprocess.run(['dbus-update-activation-environment', 'DISPLAY', 'XDG_CACHE_HOME',
                        'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'GSETTINGS_BACKEND'], env=env, check=True)
        start([str(root / 'usr/bin/speech-dispatcher'), '-s', '-t', '0', '-c', 'unix_socket',
               '-S', str(work / 'speechd.sock'), '-P', str(work / 'speechd.pid'),
               '-C', str(work / 'speech-config'), '-m', str(root / 'usr/lib/speech-dispatcher-modules'),
               '-L', str(work / 'logs')], 'speechd', env)
        for _ in range(30):
            if (work / 'speechd.sock').exists():
                break
            time.sleep(.1)
        if not (work / 'speechd.sock').exists():
            raise RuntimeError('Speech Dispatcher socket was not created')
        orca = start([str(root / 'usr/bin/orca'), '--replace', '--debug-file',
                      str(work / 'orca-debug.log'), '--user-prefs', str(work / 'prefs'),
                      '--enable', 'speech', '--disable', 'braille'], 'orca', env)
        time.sleep(3)
        if orca.poll() is not None:
            raise RuntimeError('Orca did not stay running')
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=args.chromium, headless=False,
                args=['--no-sandbox', '--force-renderer-accessibility', '--window-size=1280,1000'], env=env)
            try:
                page = browser.new_page(no_viewport=True)
                response = page.goto(args.url, wait_until='domcontentloaded')
                if not response or not response.ok:
                    raise RuntimeError('Comparison fixture could not be loaded')
                source = response.body()
                (work / 'fixture.html').write_bytes(source)
                result['url'] = page.url
                result['fixture_sha256'] = hashlib.sha256(source).hexdigest()
                result['environment']['browser_version'] = browser.version
                page.bring_to_front()
                time.sleep(3)

                def observe(label, action_description, action, expected_focus=None, message=None):
                    before = page.evaluate('({id:document.activeElement.id,tag:document.activeElement.localName})')
                    began = now()
                    action()
                    # A bounded observation window, not a claim of permanent silence.
                    time.sleep(2)
                    ended = now()
                    after = page.evaluate('({id:document.activeElement.id,tag:document.activeElement.localName})')
                    row = {'label': label, 'action': action_description, 'started_at': began,
                           'finished_at': ended, 'focus_before': before, 'focus_after': after}
                    if expected_focus:
                        row['expected_focus'] = expected_focus
                        row['focus_matched'] = after['id'] == expected_focus
                    if message:
                        row['message'] = page.locator(message).inner_text()
                    observations.append(row)
                    (work / 'timeline.json').write_text(json.dumps(observations, indent=2))
                    page.screenshot(path=str(work / (label + '.png')), full_page=True)
                    if expected_focus and not row['focus_matched']:
                        raise RuntimeError('Input did not reach expected control: ' + label)

                for number in range(1, 6):
                    observe(f'tab-{number}', 'browser.keyboard.press Tab',
                            lambda: page.keyboard.press('Tab'), f'save{number}')
                    observe(f'save-{number}', 'browser.keyboard.press Space',
                            lambda: page.keyboard.press('Space'), f'save{number}', f'#message{number}')

                def heading():
                    display.key('h', True)
                    display.key('h', False)
                observe('next-heading', 'native XTest h, handled by Orca structural navigation', heading)
                (work / 'page.html').write_text(page.content())
                result['status'] = 'observed'
            finally:
                browser.close()
    except Exception as error:
        result['error'] = str(error)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for handle in handles:
            handle.close()
        display.close()
        log_path = work / 'orca-debug.log'
        if log_path.exists():
            closed_log = log_path.read_text(errors='replace')
            result['closed_log_sha256'] = hashlib.sha256(log_path.read_bytes()).hexdigest()
            for row in observations:
                row['speech'] = speech_in_window(closed_log, row['started_at'], row['finished_at'])
                row['index_method'] = 'closed log speech timestamps, not buffered file offsets'
        result['finished_at'] = now()
        (work / 'observations.json').write_text(json.dumps(result, indent=2))
        print(json.dumps({'status': result['status'], 'error': result.get('error'),
                          'evidence': str(work), 'observations': len(observations)}, indent=2))
    return 0 if result['status'] == 'observed' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:4317/live-region-variants.html')
    parser.add_argument('--chromium', default='/usr/bin/chromium')
    parser.add_argument('--inside-private-dbus', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.inside_private_dbus:
        # Never update activation variables in an existing user's D-Bus session.
        return subprocess.call(['dbus-run-session', '--', sys.executable, str(Path(__file__).resolve()),
                                *sys.argv[1:], '--inside-private-dbus'])
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
