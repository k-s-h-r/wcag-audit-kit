"""Check known-source media bytes and timing, not ASR/sign-language accuracy."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks import core


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)],text=True))


def samples(path):
    raw=subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error','-i',str(path),'-f','f32le','-ac','1','-ar','22050','pipe:1'])
    return [x[0] for x in struct.iter_unpack('<f',raw)]


def rms(values):return math.sqrt(sum(x*x for x in values)/len(values))


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);results=[]
    root=core.ROOT/'benchmarks/cases'
    voice=samples(root/'1.4.7/public/assets/level-voice.wav')
    for variant in ['a','b']:
        bed=samples(root/f'1.4.7/public/assets/level-bed-{variant}.wav')
        mix=samples(root/f'1.4.7/public/assets/level-mix-{variant}.wav')
        assert len(voice)==len(bed)==len(mix)
        window_db=[]
        for start in range(0,len(voice),441):
            v=rms(voice[start:start+441]);b=rms(bed[start:start+441])
            if v>1e-8:
                assert b>0;window_db.append(20*math.log10(v/b))
        if variant=='a':assert max(window_db)<20
        else:assert min(window_db)>20
        error=max(abs(a+b-c) for a,b,c in zip(voice,bed,mix));assert error<1e-6
        results.append(dict(material='1.4.7 '+variant,source_window_db_min=min(window_db),source_window_db_max=max(window_db),
            mix_reconstruction_max_error=error,seconds=len(voice)/22050,scope='separate known stems, not unknown-source separation'))
    signed=root/'1.2.6';metadata=core.load(signed/'suite.json')['material_sources']
    assert hashlib.sha1((signed/'materials/Hello1.ogv').read_bytes()).hexdigest()==metadata[0]['original_sha1']
    assert core.file_hash(signed/'public/assets/sign.webm')==metadata[1]['derived_sign_sha256']
    info=probe(signed/'public/assets/sign.webm')
    assert any(s['codec_type']=='video' and s['width']==320 and s['height']==240 for s in info['streams'])
    assert not any(s['codec_type']=='audio' for s in info['streams'])
    results.append(dict(material='1.2.6',license=metadata[0]['license'],duration=float(info['format']['duration']),
        original_hash_verified=True,derived_hash_verified=True,scope='meaning from public source description; no independent interpreter review'))
    extended=root/'1.2.7';facts=core.load(extended/'suite.json')['material_sources'][0]
    video_duration=float(probe(extended/'public/assets/extended-source.webm')['format']['duration'])
    for name in ['expanded.wav','expanded-other.wav']:
        audio_duration=float(probe(extended/'public/assets'/name)['format']['duration'])
        assert audio_duration>video_duration
        assert facts['main_duration_seconds']<facts['extended_pause_after_seconds']<video_duration-.15
        results.append(dict(material='1.2.7 '+name,audio_duration=audio_duration,video_duration=video_duration,
            pause_after=facts['extended_pause_after_seconds'],scope='known utterance and time budget; browser probe checks actual pause/resume'))
    core.save(out/'observed.json',dict(scope='known-source fixture calibration, not detector accuracy',corpus_digest=core.corpus()['digest'],results=results))
    print('Known-source levels, original/derived sign hashes, and description time budget checked.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args();main(args.out)
