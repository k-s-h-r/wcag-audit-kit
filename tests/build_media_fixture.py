"""Build a known-source caption calibration fixture, without an OS installation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


SPEECH = 'Press the blue button to save the document.'


def run(command, **options):
    return subprocess.run(command, check=True, text=True, capture_output=True, **options)


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02}.{ms % 1000:03}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--espeak', type=Path, required=True)
    parser.add_argument('--library-prefix', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'LD_LIBRARY_PATH': str(args.library_prefix / 'usr/lib/x86_64-linux-gnu'),
           'ESPEAK_DATA_PATH': str(args.library_prefix / 'usr/lib/x86_64-linux-gnu')}
    run([str(args.espeak), '-v', 'en-us', '-s', '145', '-w', str(out / 'speech.wav'), SPEECH], env=env)
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json',
                           str(out / 'speech.wav')]).stdout)
    duration = float(probe['format']['duration'])
    if duration + .5 >= 5.2:
        raise ValueError('Narration overlaps the independently scheduled tone')
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(out / 'speech.wav'), '-f', 'lavfi',
         '-i', 'sine=frequency=880:duration=0.25:sample_rate=22050', '-filter_complex',
         '[0:a]adelay=500:all=1,apad=whole_dur=7[a];'
         '[1:a]volume=0.2,adelay=5500:all=1[b];'
         '[a][b]amix=inputs=2:duration=longest:normalize=0,atrim=duration=7',
         '-c:a', 'pcm_s16le', str(out / 'soundtrack.wav')])
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
         'color=c=white:s=640x360:r=30:d=7', '-i', str(out / 'soundtrack.wav'), '-vf',
         "drawtext=font=DejaVuSans:text='Saving a document':x=30:y=25:fontsize=30:fontcolor=black,"
         'drawbox=x=220:y=130:w=200:h=80:color=0x005bba:t=fill,'
         "drawtext=font=DejaVuSans:text='SAVE':x=270:y=150:fontsize=36:fontcolor=white,"
         "drawtext=font=DejaVuSans:text='Saved':x=270:y=245:fontsize=28:fontcolor=0x146b21:enable='gte(t,5.5)',"
         "drawtext=font=DejaVuSans:text='Synthetic calibration fixture':x=30:y=310:fontsize=18:fontcolor=black",
         '-c:v', 'libvpx-vp9', '-row-mt', '1', '-crf', '35', '-b:v', '0',
         '-c:a', 'libopus', '-b:a', '64k', '-t', '7', str(out / 'clip.webm')])
    first_end = duration + .7
    captions = {
        'good': f'00:00:00.400 --> {stamp(first_end)}\n[Narrator] {SPEECH}\n\n'
                '00:00:05.400 --> 00:00:06.400\n[Confirmation tone]\n',
        'wrong-text': f'00:00:00.400 --> {stamp(first_end)}\n[Narrator] Press the red button to delete the document.\n\n'
                      '00:00:05.400 --> 00:00:06.400\n[Confirmation tone]\n',
        'late': '00:00:04.800 --> 00:00:06.900\n[Narrator] ' + SPEECH + '\n\n'
                '00:00:05.400 --> 00:00:06.400\n[Confirmation tone]\n',
    }
    template = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Caption comparison: VARIANT</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font:20px/1.6 sans-serif;margin:2rem}video{width:640px;max-width:100%;display:block;background:#fff}button{font:inherit;margin:.5rem;padding:.5rem}button:focus-visible{outline:4px solid #005bba;outline-offset:4px}</style>
<main><h1>Caption comparison: VARIANT</h1><p>A short prerecorded demonstration. Use Play and Captions to inspect the presentation.</p>
<video id="clip" preload="auto"><source src="clip.webm" type="video/webm"><track id="caption-track" kind="captions" src="VARIANT.vtt" srclang="en" label="English"></video>
<button id="play" type="button">Play video</button><button id="captions" type="button" aria-pressed="false">Captions</button><span id="caption-state">Off</span>
</main><script src="player.js"></script></html>'''
    for name, text in captions.items():
        (out / (name + '.vtt')).write_text('WEBVTT\n\n' + text)
        (out / (name + '.html')).write_text(template.replace('VARIANT', name))
    (out / 'player.js').write_text('''const video=document.querySelector('#clip');
document.querySelector('#play').addEventListener('click',()=>{if(video.paused)video.play();else video.pause()});
video.addEventListener('play',()=>document.querySelector('#play').textContent='Pause video');
video.addEventListener('pause',()=>document.querySelector('#play').textContent='Play video');
document.querySelector('#captions').addEventListener('click',()=>{
 const showing=video.textTracks[0].mode!=='showing';
 video.textTracks[0].mode=showing?'showing':'hidden';
 document.querySelector('#captions').setAttribute('aria-pressed',String(showing));
 document.querySelector('#caption-state').textContent=showing?'On':'Off';
});
''')
    provenance = {'kind': 'known-source synthetic calibration, not a blind accuracy evaluation',
        'intended_narration': SPEECH, 'speech_duration_seconds': duration,
        'narration_audio_interval': [.5, duration + .5], 'tone_audio_interval': [5.5, 5.75],
        'generated_by': run([str(args.espeak), '--version'], env=env).stdout.strip(),
        'ffmpeg_version': run(['ffmpeg', '-version']).stdout.splitlines()[0],
        'source_probe': probe, 'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted(out.iterdir()) if p.is_file()}}
    (out / 'source-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'out': str(out), 'speech_duration_seconds': duration, 'video_duration_seconds': 7}))


if __name__ == '__main__':
    main()
