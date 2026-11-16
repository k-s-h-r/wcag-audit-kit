"""Observe real caption controls and playback. No speech/content/flash judgement."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import time

from browser_capture import capture_image
from collection_checkpoint import save_json_atomic
from input_observation import locator_for
from screen_reader_native import origin


PLAYER = """video => ({currentTime:Number.isFinite(video.currentTime)?video.currentTime:null,
 duration:Number.isFinite(video.duration)?video.duration:null,
 paused:video.paused,ended:video.ended,muted:video.muted,volume:video.volume,
 playbackRate:video.playbackRate,readyState:video.readyState,currentSrc:video.currentSrc,
 error:video.error?{code:video.error.code,message:video.error.message}:null,
 played:Array.from({length:video.played.length},(_,i)=>[video.played.start(i),video.played.end(i)]),
 quality:(()=>{const q=video.getVideoPlaybackQuality?.();return q?{
  creationTime:q.creationTime,totalVideoFrames:q.totalVideoFrames,droppedVideoFrames:q.droppedVideoFrames,
  corruptedVideoFrames:q.corruptedVideoFrames??null}:null})(),
 tracks:[...video.textTracks].map(t=>({kind:t.kind,label:t.label,language:t.language,mode:t.mode,
 cues:t.cues?[...t.cues].map(c=>({start:c.startTime,end:c.endTime,text:c.text})):null,
 activeCues:t.activeCues?[...t.activeCues].map(c=>({start:c.startTime,end:c.endTime,text:c.text})):null}))})"""
OBSERVER = """video=>{
 for(const event of ['play','pause','ended','waiting','seeking','seeked','error'])
  video.addEventListener(event,()=>window.__wcagMedia({event,at:performance.now(),currentTime:video.currentTime}));
 if(video.requestVideoFrameCallback){
  const frame=(now,metadata)=>{
   window.__wcagMedia({event:'frame',at:now,currentTime:video.currentTime,mediaTime:metadata.mediaTime,
    presentedFrames:metadata.presentedFrames,expectedDisplayTime:metadata.expectedDisplayTime,
    tracks:[...video.textTracks].map(t=>({mode:t.mode,language:t.language,
     activeCues:t.activeCues?[...t.activeCues].map(c=>({start:c.startTime,end:c.endTime,text:c.text})):null}))});
   video.requestVideoFrameCallback(frame);
  };video.requestVideoFrameCallback(frame);
 }
}"""


def now():
    return datetime.now(timezone.utc).isoformat()


async def run(args):
    request_bytes = args.request.read_bytes()
    request = json.loads(request_bytes)
    if not isinstance(request.get('case_id'), str) or not request['case_id'].strip():
        raise ValueError('case_idが必要')
    allowed = request.get('allowed_origins', [origin(request['url'])])
    if not isinstance(allowed, list) or any(origin(value) != value for value in allowed) or origin(request['url']) not in allowed:
        raise ValueError('対象のallowed_originsが必要')
    limit = request.get('event_limit', 100000)
    seconds = request.get('max_seconds', 60)
    if type(limit) is not int or not 1 <= limit <= 1000000 or type(seconds) not in {int, float} or not 1 <= seconds <= 86400:
        raise ValueError('event_limit又はmax_secondsが範囲外')
    times = request.get('screenshot_times', [])
    if not isinstance(times, list) or any(type(value) not in {int, float} or not math.isfinite(value) or value < 0 for value in times):
        raise ValueError('screenshot_timesは媒体の時刻の数値配列にする')
    actions = request.get('prepare_actions', []) + [request['play_action']]
    for action in actions:
        if action.get('type') not in {'click', 'press', 'wait_for'}:
            raise ValueError('実際のUIのclick・press・wait_forを指定する')
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    events = []
    dropped = 0
    result = {'status': 'blocked', 'case_id': request['case_id'], 'started_at': now(),
        'request_sha256': hashlib.sha256(request_bytes).hexdigest(), 'actions': [], 'screenshots': [],
        'listening_performed': False, 'speech_meaning_reviewed': False, 'non_speech_meaning_reviewed': False,
        'all_visual_frames_reviewed': False, 'flash_thresholds_reviewed': False, 'wcag_judgement': None,
        'note': '再生・字幕の実表示の観察。endedや字幕トラックの存在から意味・全区間の合格を作らない。'}
    result['scenario'] = request
    code = 2

    def accept(source, event):
        nonlocal dropped
        if len(events) < limit:
            events.append(dict(event, frame_url=source['frame'].url, received_at=now()))
        else:
            dropped += 1

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            try:
                context = await browser.new_context(viewport=request.get('viewport', {'width': 1280, 'height': 900}),
                    locale=request.get('locale', 'en-US'), storage_state=(str((args.request.resolve().parent / request['auth_state']).resolve())
                                                           if request.get('auth_state') else None))
                await context.expose_binding('__wcagMedia', accept)
                page = await context.new_page()
                await page.goto(request['url'], wait_until='domcontentloaded')

                def scope():
                    if origin(page.url) not in allowed:
                        raise ValueError('検証範囲外へ移動した')

                scope()
                media = locator_for(page, request['media'])
                await media.evaluate(OBSERVER)
                result['browser_version'] = browser.version
                result['before'] = await media.evaluate(PLAYER)
                await capture_image(page, output / 'before.png', full_page=True)
                for action in actions:
                    began = now()
                    if action['type'] == 'press':
                        await page.keyboard.press(action['key'])
                    elif action['type'] == 'wait_for':
                        await locator_for(page, action).wait_for(state=action.get('state', 'visible'))
                    else:
                        await locator_for(page, action).click()
                    scope()
                    result['actions'].append({'action': action, 'started_at': began, 'observed_at': now(),
                                              'player': await media.evaluate(PLAYER)})
                    save_json_atomic(output / 'caption-player.json', result)
                pending = list(sorted(set(times)))
                began = time.monotonic()
                while time.monotonic() - began < seconds:
                    scope()
                    player = await media.evaluate(PLAYER)
                    while pending and player['currentTime'] >= pending[0]:
                        requested = pending.pop(0)
                        name = f'caption-{len(result["screenshots"]) + 1}.png'
                        await capture_image(page, output / name, full_page=True)
                        after = await media.evaluate(PLAYER)
                        result['screenshots'].append({'path': name, 'requested_media_time': requested,
                            'before_capture': player, 'after_capture': after,
                            'note': '画像取得中も再生は進む。要求時刻の厳密なフレームとは限らない。'})
                    if player['ended']:
                        break
                    await page.wait_for_timeout(100)
                result['after'] = await media.evaluate(PLAYER)
                result['playback_ended'] = result['after']['ended']
                result['unreached_screenshot_times'] = pending
                (output / 'page.html').write_text(await page.content())
                result['status'] = 'collected' if result['playback_ended'] and not pending and not dropped else 'partial'
                code = 0 if result['status']=='collected' else 2
            finally:
                await browser.close()
    except Exception as error:
        result['status'] = 'blocked'
        result['error'] = str(error)
        code = 2
    finally:
        result['finished_at'] = now()
        result['event_trace'] = {'events': len(events), 'truncated': bool(dropped), 'dropped': dropped}
        if dropped and result['status']=='collected':
            result['status']='partial'
            code=2
        frames = [event for event in events if event.get('event') == 'frame']
        result['frame_callbacks'] = {'count': len(frames), 'first_media_time': frames[0]['mediaTime'] if frames else None,
            'last_media_time': frames[-1]['mediaTime'] if frames else None,
            'note': 'コールバック数や再生終了だけで、AIが全フレームを視認・理解したことにはしない。'}
        save_json_atomic(output / 'media-events.json', events)
        save_json_atomic(output / 'caption-player.json', result)
        print(json.dumps({'status': result['status'], 'error': result.get('error'), 'evidence': str(output)}, ensure_ascii=False))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except (ValueError, KeyError, FileNotFoundError) as error:
        print('ERROR:', error)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
