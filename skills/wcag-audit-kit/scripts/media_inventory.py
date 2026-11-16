"""Inspect media streams and decode them; this does not review their meaning."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from collection_checkpoint import save_json_atomic


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--captions', type=Path, action='append', default=[])
    parser.add_argument('--frame-hashes', action='store_true')
    args = parser.parse_args()
    source = args.media.resolve()
    if not source.is_file():
        raise ValueError('実在する媒体ファイルが必要')
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'blocked', 'source': str(source), 'source_sha256': file_hash(source),
        'source_bytes': source.stat().st_size, 'started_at': datetime.now(timezone.utc).isoformat(),
        'speech_meaning_reviewed': False, 'non_speech_meaning_reviewed': False,
        'visual_meaning_reviewed': False, 'captions_meaning_reviewed': False,
        'flash_thresholds_reviewed': False, 'wcag_judgement': None}
    code = 2
    try:
        command = ['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(source)]
        probe = subprocess.run(command, text=True, capture_output=True, check=True)
        (output / 'ffprobe.json').write_text(probe.stdout)
        metadata = json.loads(probe.stdout)
        result['duration_seconds'] = float(metadata['format']['duration']) if 'duration' in metadata.get('format', {}) else None
        result['streams'] = [{'index': stream['index'], 'type': stream.get('codec_type'),
            'codec': stream.get('codec_name'), 'language': stream.get('tags', {}).get('language'),
            'disposition': stream.get('disposition', {})} for stream in metadata['streams']]
        command = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-xerror',
                   '-i', str(source), '-map', '0:v?', '-map', '0:a?', '-progress', 'pipe:1', '-nostats', '-f', 'null', '-']
        decoded = subprocess.run(command, text=True, capture_output=True)
        (output / 'decode-progress.txt').write_text(decoded.stdout)
        (output / 'decode-errors.txt').write_text(decoded.stderr)
        result['decode_exit_code'] = decoded.returncode
        if decoded.returncode:
            raise ValueError('選択した全映像・音声ストリームのデコードが完了しない')
        result['all_video_and_audio_streams_decoded'] = True
        result['frame_hashes'] = []
        if args.frame_hashes:
            for video, stream in enumerate(s for s in metadata['streams'] if s.get('codec_type') == 'video'):
                destination = output / f'video-{video}.frames.sha256.txt'
                command = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-xerror',
                    '-i', str(source), '-map', f'0:v:{video}', '-pix_fmt', 'rgba', '-f', 'framemd5', '-hash', 'sha256', '-']
                with destination.open('w') as handle:
                    subprocess.run(command, text=True, stdout=handle, stderr=subprocess.PIPE, check=True)
                hashes = [line.split(',')[-1].strip() for line in destination.read_text().splitlines()
                          if line.strip() and not line.startswith('#')]
                result['frame_hashes'].append({'stream_index': stream['index'], 'file': destination.name,
                    'decoded_frames': len(hashes), 'unique_hashes': len(set(hashes)),
                    'adjacent_hash_changes': sum(a != b for a, b in zip(hashes, hashes[1:])),
                    'representation': 'decoded RGBA 8-bit, SHA-256 per frame',
                    'note': '全復号フレームの比較。HDR・アルファ・色変換・プレーヤー等の重ね合わせを含む正式な閃光判定ではない。'})
        result['captions'] = []
        for index, path in enumerate(args.captions, 1):
            copied = output / f'captions-{index}{path.suffix}'
            copied.write_bytes(path.read_bytes())
            result['captions'].append({'original_path': str(path.resolve()), 'copied': copied.name,
                                       'sha256': file_hash(copied), 'content_reviewed': False})
        if file_hash(source) != result['source_sha256']:
            raise ValueError('調査中に媒体ファイルが変更された')
        result['status'] = 'collected'
        code = 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        result['error'] = str(error)
    finally:
        result['finished_at'] = datetime.now(timezone.utc).isoformat()
        save_json_atomic(output / 'media.json', result)
        print(json.dumps({'status': result['status'], 'error': result.get('error'), 'evidence': str(output)}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
