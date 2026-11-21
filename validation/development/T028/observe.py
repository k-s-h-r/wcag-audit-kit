"""Observe selected media facts in local fixtures using actual playback and decoded audio."""

import argparse
from array import array
from datetime import datetime, timezone
from functools import partial
from hashlib import sha256
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from math import sqrt
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
import sys
from threading import Thread
from urllib.parse import urljoin
from urllib.request import ProxyHandler, build_opener
import wave


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = HERE.parents[1] / 'media/source'
PLAYER = REPO / 'skills/wcag-audit-kit/scripts/caption_player_probe.py'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    with path.open('rb') as file:
        from hashlib import file_digest
        return file_digest(file, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def command(logs, name, *args):
    began = now()
    argv = list(map(str, args))
    process = subprocess.run(argv, capture_output=True, text=True)
    (logs / f'{name}.stdout').write_text(process.stdout, encoding='utf-8')
    (logs / f'{name}.stderr').write_text(process.stderr, encoding='utf-8')
    save(logs / f'{name}.json', {'command': argv, 'started_at': began,
                                'finished_at': now(), 'exit_code': process.returncode})
    if process.returncode:
        raise RuntimeError(f'{name} exited {process.returncode}. See {logs / (name + ".stderr")}')
    return process.stdout.strip()


def ffmpeg(logs, name, *args):
    return command(logs, name, 'ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', *args)


def clips(source, destination, logs, description):
    visual = destination.parent / 'description-visual.webm'
    ffmpeg(logs, 'extend-visual', '-i', source, '-map', '0:v:0', '-an',
           '-vf', 'tpad=stop_mode=clone:stop_duration=1', '-c:v', 'libvpx-vp9',
           '-deadline', 'good', '-cpu-used', '3', '-pix_fmt', 'yuv420p', visual)
    duration = str(description['duration'])
    delay = round(description['speech_starts'] * 1000)
    voice = f"flite=text={description['spoken_description']}:voice=slt"
    mix = (f'[1:a]apad=whole_dur={duration}[original];'
           f'[2:a]atempo=1.15,adelay={delay}:all=1[description];'
           '[original][description]amix=inputs=2:duration=first:normalize=0[a]')
    common = ('-map', '0:v:0', '-t', duration, '-c:v', 'copy', '-c:a', 'libopus', '-b:a', '96k')
    ffmpeg(logs, 'mix-description', '-i', visual, '-i', source, '-f', 'lavfi', '-i', voice,
           '-filter_complex', mix, *common, '-map', '[a]', destination / 'description-a.webm')
    ffmpeg(logs, 'pad-comparison', '-i', visual, '-i', source, '-af', f'apad=whole_dur={duration}',
           *common, '-map', '1:a:0', destination / 'description-b.webm')


def prepare(output, logs, scope):
    original = read(SOURCE / 'source-provenance.json')['files']
    if original['clip.webm'] != scope['source_video_sha256'] or any(
            digest(SOURCE / path) != checksum for path, checksum in original.items()):
        raise ValueError('Original media or caption fixture changed.')
    public = output / 'public'
    public.mkdir()
    for path in ['clip.webm', 'player.js', *[name + ext for name in scope['captions']['cases'] for ext in ('.html', '.vtt')]]:
        shutil.copyfile(SOURCE / path, public / path)
    clips(public / 'clip.webm', public, logs, scope['description'])
    template = Template((HERE / 'fixture/player.html').read_text())
    for group in ('transcript', 'description'):
        for case in scope[group]['cases']:
            transcript = (HERE / 'fixture' / (case + '.html')).read_text() if group == 'transcript' else ''
            video = 'clip.webm' if group == 'transcript' else case + '.webm'
            (public / (case + '.html')).write_text(template.substitute(video=video, transcript=transcript))
    return public


def words(value):
    return ' '.join(re.findall(r'[a-z0-9]+', value.lower()))


def decode(public, output, logs, engine, model, name, video, window=None):
    path = public / video
    audio = output / f'{name}.wav'
    ffmpeg(logs, name + '-decode', '-i', path, '-map', '0:a:0', '-ar', '16000', '-ac', '1',
           '-c:a', 'pcm_s16le', audio)
    prefix = output / name
    command(logs, name + '-whisper', engine, '-m', model, '-f', audio, '-l', 'en', '-t', '4',
            '-ojf', '-otxt', '-of', prefix)
    decoded = read(prefix.with_suffix('.json'))['transcription']
    with wave.open(str(audio), 'rb') as wav:
        if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (16000, 1, 2):
            raise ValueError('Unexpected decoded audio format.')
        frames = wav.getnframes()
        rms = None
        if window:
            start, end = (round(t * 16000) for t in window)
            wav.setpos(start)
            samples = array('h', wav.readframes(end - start))
            if sys.byteorder != 'little':
                samples.byteswap()
            if len(samples) != end - start:
                raise ValueError('The selected audio window is truncated.')
            rms = sqrt(sum((sample / 32768) ** 2 for sample in samples) / len(samples))
    return {'video': video, 'media_sha256': digest(path), 'wave_sha256': digest(audio), 'frames': frames,
            'segments': [{'text': entry['text'].strip(), 'asr_offsets_ms': entry['offsets']} for entry in decoded],
            'tail_rms': rms}


def text(utterances):
    return ' '.join(row['text'] for row in utterances['segments'])


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def active_cues(state):
    return [cue['text'] for track in state['tracks'] if track['kind'] == 'captions' and track['mode'] == 'showing'
            for cue in track['activeCues'] or []]


def playback(server_origin, logs, output, media, page, times, captions=False):
    request = {'case_id': 't028-' + page, 'url': server_origin + page + '.html', 'media': {'selector': '#clip'},
               'prepare_actions': [{'type': 'click', 'selector': '#captions'}] if captions else [],
               'play_action': {'type': 'click', 'selector': '#play'}, 'screenshot_times': times, 'max_seconds': 15}
    request_path = output / (page + '-request.json')
    save(request_path, request)
    folder = output / page
    command(logs, page + '-browser', sys.executable, PLAYER, '--request', request_path, '--out', folder)
    observed = read(folder / 'caption-player.json')
    trace = read(folder / 'media-events.json')
    after = observed['after']
    resource_url = urljoin(server_origin, media['video'])
    with build_opener(ProxyHandler({})).open(resource_url, timeout=5) as response:
        fetched = sha256(response.read()).hexdigest()
    if (observed['status'] != 'collected' or observed['request_sha256'] != digest(request_path)
            or observed['scenario'] != request or observed['event_trace']['events'] != len(trace)
            or observed['event_trace']['truncated'] or not observed['playback_ended']
            or not any(row['event'] == 'ended' for row in trace) or after['currentSrc'] != resource_url
            or after['error'] is not None or after['muted'] or after['volume'] <= 0
            or fetched != media['media_sha256']):
        raise ValueError(f'{page} playback, source or trace is unverified.')
    samples = []
    for shot, time in zip(observed['screenshots'], times, strict=True):
        before, end = shot['before_capture'], shot['after_capture']
        if (shot['requested_media_time'] != time or not time <= before['currentTime'] <= time + 0.25
                or not before['currentTime'] <= end['currentTime'] <= time + 0.60
                or active_cues(before) != active_cues(end)):
            raise ValueError(f'{page} sample at {time} has insufficient timing or cue evidence.')
        samples.append({'requested': time, 'observed': [before['currentTime'], end['currentTime']],
                        'active_cues': active_cues(before), 'screen': (folder / shot['path']).relative_to(output).as_posix(),
                        'screen_sha256': digest(folder / shot['path'])})
    return {'status': 'collected', 'browser': observed['browser_version'], 'url': request['url'], 'source_url': resource_url,
            'media_sha256': fetched, 'record': (folder / 'caption-player.json').relative_to(output).as_posix(),
            'trace': (folder / 'media-events.json').relative_to(output).as_posix(), 'samples': samples,
            'video_quality': after['quality']}


class Transcript(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.active = False
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'section' and dict(attrs).get('id') == 'transcript':
            self.active = True

    def handle_endtag(self, tag):
        if tag == 'section':
            self.active = False

    def handle_data(self, value):
        if self.active and value.strip():
            self.text.append(value.strip())


def caption_outcome(row, speech, different):
    first, second, _ = [shot['active_cues'] for shot in row['samples']]
    selected = [[words(cue.removeprefix('[Narrator]')) for cue in cues] for cues in (first, second)]
    if selected == [[speech], [speech]]:
        return 'matches'
    if selected == [[different], [different]]:
        return 'different-words'
    if selected == [[], []]:
        return 'absent-at-samples'
    return 'cant_tell'


def compare(scope, public, logs, output, engine, model):
    audio_path = output / 'audio'
    audio_path.mkdir()
    source = decode(public, audio_path, logs, engine, model, 'source', 'clip.webm')
    pair = {case: decode(public, audio_path, logs, engine, model, case, case + '.webm', scope['description']['audio_window'])
            for case in scope['description']['cases']}
    for candidate in pair.values():
        candidate['decoded_video_hash'] = ffmpeg(logs, candidate['video'] + '-video-hash', '-i', public / candidate['video'],
                                                  '-map', '0:v:0', '-pix_fmt', 'rgba', '-f', 'hash', '-hash', 'sha256', '-')
    results = {}
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=public)) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f'http://127.0.0.1:{server.server_port}/'
            for case in scope['captions']['cases']:
                row = playback(origin, logs, output, source, case, scope['captions']['samples'], captions=True)
                speech = words(text(source))
                valid = speech == words(scope['captions']['source_speech'])
                outcome = caption_outcome(row, speech, words(scope['captions']['different_speech'])) if valid else 'cant_tell'
                results[case] = {**row, 'outcome': outcome}
            for case in scope['transcript']['cases']:
                row = playback(origin, logs, output, source, case, [scope['transcript']['sample']])
                transcript = Transcript((output / case / 'page.html').read_text()).text
                outcome = ('includes-visual-fact' if scope['transcript']['visual_fact'] in transcript else 'omits-visual-fact')
                results[case] = {**row, 'outcome': outcome if transcript else 'cant_tell', 'transcript': transcript}
            normal, control = (pair[name] for name in scope['description']['cases'])
            description_words = words(scope['description']['spoken_description'])
            matched = (description_words in words(text(normal)) and description_words not in words(text(control))
                       and normal['decoded_video_hash'] == control['decoded_video_hash']
                       and control['tail_rms'] <= scope['description']['comparison_max_rms'] < normal['tail_rms'])
            for case in scope['description']['cases']:
                row = playback(origin, logs, output, pair[case], case, scope['description']['samples'])
                includes = description_words in words(text(pair[case]))
                outcome = ('includes-description' if includes else 'omits-description') if matched else 'cant_tell'
                results[case] = {**row, 'outcome': outcome}
        finally:
            server.shutdown()
            thread.join()
    expected = {case: outcome for group in ('captions', 'transcript', 'description') for case, outcome in scope[group]['cases'].items()}
    return {'correct': sum(results[case]['outcome'] == expected[case] for case in expected), 'total': len(expected),
            'cases': results, 'audio': {'original': source, **pair}, 'wcag_judgement': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--whisper-source', required=True, type=Path)
    parser.add_argument('--whisper-cli', required=True, type=Path)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    logs = output / 'commands'
    logs.mkdir()
    scope_path = HERE / 'scope.json'
    scope = read(scope_path)
    shutil.copyfile(scope_path, output / 'scope.json')
    commit = command(logs, 'whisper-commit', 'git', '-C', args.whisper_source, 'rev-parse', 'HEAD')
    model_hash = digest(args.model)
    if commit != scope['whisper']['commit'] or model_hash != scope['whisper']['sha256']:
        raise ValueError('Unexpected Whisper source revision or model SHA-256.')
    public = prepare(output, logs, scope)
    result = compare(scope, public, logs, output, args.whisper_cli.resolve(), args.model.resolve())
    save(output / 'observed.json', {**result, 'scope_sha256': digest(scope_path), 'whisper_commit': commit,
                                   'model_sha256': model_hash, 'binary_sha256': digest(args.whisper_cli),
                                   'source_files': {file.name: digest(file) for file in public.iterdir()}})
    print(f'{result["correct"]}/{result["total"]} selected observations matched')
    return 0 if result['correct'] == result['total'] else 2


if __name__ == '__main__':
    sys.exit(main())
