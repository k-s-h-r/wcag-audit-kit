"""Measure media operation in bounded benchmark fixtures using Chromium."""
import re
from urllib.parse import urlsplit


TRANSCRIPT = {'1.2.1', '1.2.3', '1.2.8'}
FIELDS = {
    **{criterion: {'target', 'region'} for criterion in TRANSCRIPT},
    '1.2.2': {'target', 'captions', 'play'},
    '1.2.5': {'target', 'select'},
    '1.4.2': {'target', 'region'},
}
ID = re.compile(r'#[A-Za-z][A-Za-z0-9_-]{0,79}')
ALTERNATIVE_LABEL = re.compile(r'文章代替|文字起こし|文字による代替|\btranscript\b', re.I)
MEDIA_SNAPSHOT = """e => ({
  source: e.currentSrc, ready: e.readyState, position: e.currentTime,
  duration: Number.isFinite(e.duration) ? e.duration : null, paused: e.paused,
  ended: e.ended, muted: e.muted, volume: e.volume, autoplay: e.autoplay,
  controls: e.controls, error: e.error?.code ?? null,
  activated: navigator.userActivation.hasBeenActive,
  visible: e.checkVisibility({checkVisibilityCSS:true, checkOpacity:true})
           && e.getBoundingClientRect().width > 0 && e.getBoundingClientRect().height > 0,
  audioBytes: e.webkitAudioDecodedByteCount ?? 0, videoBytes: e.webkitVideoDecodedByteCount ?? 0,
  height: e.videoHeight ?? null,
  played: Array.from({length:e.played.length}, (_,i) => [e.played.start(i), e.played.end(i)])
})"""
REGION_SCAN = """(scope, selector) => {
  // An absence decision is limited to a single plain container owning the
  // media. Links, custom controls and richer markup require another procedure.
  const all = Array.from(scope.children);
  const target = scope.querySelector(selector);
  const text = Array.from(scope.childNodes).some(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
  const onlyPlainHeadings = all.every(e => e === target ||
    (/^H[1-6]$/.test(e.tagName) && !e.childElementCount && !e.attributes.length));
  return {
    mediaInside: !!target && target.parentElement === scope,
    plainMediaOnly: scope === document.querySelector('main') && scope.parentElement === document.body
                  && document.body.children.length === 1 && document.scripts.length === 0
                  && !text && !!target && !target.childElementCount && onlyPlainHeadings,
    disclosures: Array.from(scope.querySelectorAll('details > summary:first-of-type'), (e, index) => ({
      index, label: e.getAttribute('aria-label') || e.innerText,
      visible: e.checkVisibility({checkVisibilityCSS:true, checkOpacity:true})
    }))
  };
}"""
PLAYBACK_SAMPLE = """async e => {
  const context = new AudioContext();
  const stream = e.captureStream();
  try {
    const tracks = stream.getAudioTracks();
    if (tracks.length !== 1) return [];
    const analyser = context.createAnalyser();
    context.createMediaStreamSource(stream).connect(analyser);
    await context.resume();
    const values = new Float32Array(analyser.fftSize);
    const samples = [];
    for (let i = 0; i < 18; i++) {
      await new Promise(resolve => setTimeout(resolve, 200));
      analyser.getFloatTimeDomainData(values);
      samples.push({
        at: performance.now(), position: e.currentTime, paused: e.paused,
        muted: e.muted, volume: e.volume, peak: Math.max(...values.map(Math.abs))
      });
    }
    return samples;
  } finally {
    for (const track of stream.getTracks()) track.stop();
    await context.close();
  }
}"""


def validate_plan(criterion, plan):
    if criterion not in FIELDS or not isinstance(plan, dict) or set(plan) != FIELDS[criterion]:
        raise ValueError('メディア観測の公開手順に必要な項目がそろっていない')
    for key, value in plan.items():
        allowed = key == 'region' and value == 'main'
        if not isinstance(value, str) or not (allowed or ID.fullmatch(value)):
            raise ValueError('メディア観測の対象には個別のIDまたはmainを指定する')
    if len(set(plan.values())) != len(plan):
        raise ValueError('観測対象と操作対象には別のIDを指定する')


def launch_args(criterion, plan):
    return ['--autoplay-policy=no-user-gesture-required'] if criterion == '1.4.2' else []


async def unique(page, selector):
    locator = page.locator(selector)
    if await locator.count() != 1:
        raise ValueError('メディア観測で指定した要素を一つに特定できない')
    return locator


async def media_snapshot(media):
    return await media.evaluate(MEDIA_SNAPSHOT)


async def wait_for(page, target, predicate, timeout):
    # All predicates are fixed in code. The fixture plan supplies a selector.
    await page.wait_for_function(
        '(selector) => { const e = document.querySelector(selector); return e && (' + predicate + '); }',
        arg=target, timeout=timeout,
    )


async def transcript(page, plan):
    region = await unique(page, plan['region'])
    scan = await region.evaluate(REGION_SCAN, plan['target'])
    candidates = [item for item in scan['disclosures']
                  if item['visible'] and ALTERNATIVE_LABEL.search(item['label'])]
    scan['alternatives'] = []
    for item in candidates[:10]:
        summary = region.locator('details > summary:first-of-type').nth(item['index'])
        await summary.click(timeout=1500)
        scan['alternatives'].append(await summary.evaluate("""e => ({
          open: e.parentElement.open,
          visibleText: Array.from(e.parentElement.children)
            .filter(n => n !== e && n.checkVisibility({checkVisibilityCSS:true, checkOpacity:true}))
            .map(n => n.innerText.trim()).filter(Boolean).join(' ')
        })"""))
    return scan


async def captions(page, media, plan):
    button = await unique(page, plan['captions'])
    play = await unique(page, plan['play'])
    before = await media_snapshot(media)
    initially_pressed = await button.get_attribute('aria-pressed')
    await button.click(timeout=1500)
    await play.click(timeout=1500)
    # Wait for natural playback to reach a cue. Track mode and active cue
    # membership are observed together with media time from the same sample.
    await wait_for(page, plan['target'],
                   '!e.paused && e.currentTime > 0.2 && [...e.textTracks].some(t => t.activeCues?.length)',
                   8000)
    playback = await media_snapshot(media)
    cues = await media.evaluate("""e => [...e.textTracks].map(t => ({
        kind:t.kind, mode:t.mode, sampledAt:e.currentTime,
        active:Array.from(t.activeCues || [], q => ({start:q.startTime,end:q.endTime,text:q.text}))
    }))""")
    return dict(before=before, playback=playback, cues=cues, initially_pressed=initially_pressed,
                pressed=await button.get_attribute('aria-pressed'))


async def description(page, media, plan):
    button = await unique(page, plan['select'])
    await wait_for(page, plan['target'], 'e.readyState >= 1 && !!e.currentSrc', 4000)
    before = await media_snapshot(media)
    initially_pressed = await button.get_attribute('aria-pressed')
    await button.click(timeout=1500)
    # This click selects the resource. Playback verifies the decoded source;
    # it does not count as verification of the player's own play button.
    await media.evaluate('e => e.play()')
    await wait_for(page, plan['target'], 'e.ended', 15000)
    playback = await media_snapshot(media)
    resources = await page.evaluate("""async urls => {
      const digests = [];
      for (const source of urls) {
        const url = new URL(source);
        if (url.origin !== location.origin || !crypto.subtle) return [];
        const response = await fetch(url, {redirect:'error'});
        if (!response.ok) return [];
        const bytes = await response.arrayBuffer();
        const hash = await crypto.subtle.digest('SHA-256', bytes);
        digests.push(Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, '0')).join(''));
      }
      return digests;
    }""", [before['source'], playback['source']])
    return dict(before=before, playback=playback, resources=resources, initially_pressed=initially_pressed,
                pressed=await button.get_attribute('aria-pressed'))


def user_agent_buttons(node):
    for child in node.get('children', []):
        pairs = iter(child.get('attributes', []))
        attrs = dict(zip(pairs, pairs))
        if (attrs.get('pseudo') == '-webkit-media-controls-play-button' and 'disabled' not in attrs
                and attrs.get('aria-hidden') != 'true'):
            yield child['backendNodeId']
        yield from user_agent_buttons(child)


async def native_pause(page, target):
    session = await page.context.new_cdp_session(page)
    try:
        root = (await session.send('DOM.getDocument'))['root']['nodeId']
        node = await session.send('DOM.querySelector', {'nodeId': root, 'selector': target})
        node = (await session.send('DOM.describeNode', dict(node, depth=-1, pierce=True)))['node']
        roots = [child for child in node.get('shadowRoots', []) if child['shadowRootType'] == 'user-agent']
        buttons = [button for root in roots for button in user_agent_buttons(root)]
        if len(buttons) != 1:
            return None
        quad = (await session.send('DOM.getContentQuads', {'backendNodeId': buttons[0]}))['quads']
        if len(quad) != 1:
            return None
        coordinates = [sum(quad[0][offset::2]) / 4 for offset in (0, 1)]
        await page.mouse.click(*coordinates)
        return coordinates
    finally:
        await session.detach()


async def autoplay(page, media, plan):
    await wait_for(page, plan['target'], '!e.paused && e.readyState >= 2', 4000)
    before = await media_snapshot(media)
    media_samples = await media.evaluate(PLAYBACK_SAMPLE)
    playback = await media_snapshot(media)
    region = await unique(page, plan['region'])
    scan = await region.evaluate(REGION_SCAN, plan['target'])
    coordinates = await native_pause(page, plan['target']) if playback['controls'] else None
    paused = await media_snapshot(media) if coordinates is not None else None
    return dict(before=before, playback=playback, samples=media_samples, scope=scan, pause=coordinates, after=paused)


async def capture(criterion, page, plan):
    validate_plan(criterion, plan)
    media = await unique(page, plan['target'])
    if await media.evaluate('e => e instanceof HTMLMediaElement') is not True:
        raise ValueError('指定した対象は音声または動画の要素ではない')
    if criterion in TRANSCRIPT:
        return dict(media=await media_snapshot(media), scope=await transcript(page, plan))
    if criterion == '1.2.2':
        return await captions(page, media, plan)
    if criterion == '1.2.5':
        return await description(page, media, plan)
    return await autoplay(page, media, plan)


def assess_transcript(evidence):
    scan = evidence['scope']
    if not scan['mediaInside'] or not evidence['media']['source']:
        return 'cant_tell', '同じ領域に含まれるメディアの代替経路を照合できない。'
    if any(row['open'] and row['visibleText'] for row in scan['alternatives']):
        return 'passed', '代替として表示された開閉部品を操作し、展開された文章へ到達した。文章の内容は別途確認する。'
    if scan['plainMediaOnly']:
        return 'failed', '収録した単一メディアと見出しだけの文書で、文章による代替への経路が見つからない。'
    return 'cant_tell', '文章代替への経路を特定できない。別の部品や経路を確認する。'


def assess_captions(evidence):
    before, playback = evidence['before'], evidence['playback']
    if (playback['paused'] or playback['error'] or playback['height'] <= 0 or not playback['visible']
            or evidence['initially_pressed'] != 'false' or evidence['pressed'] != 'true'
            or playback['position'] <= before['position'] or playback['videoBytes'] <= 0):
        return 'cant_tell', '字幕操作を行った状態で、動画の実再生を確認できない。'
    tracks = [t for t in evidence['cues'] if t['kind'] in {'captions', 'subtitles'}]
    active = [t for t in tracks if any(
        q['text'].strip() and q['start'] <= t['sampledAt'] < q['end'] for q in t['active']
    )]
    if any(t['mode'] == 'showing' for t in active):
        return 'passed', '動画の再生時刻に対応する字幕キューを、表示モードのトラックで取得した。'
    if active and all(t['mode'] == 'hidden' for t in active) and not any(t['mode'] == 'showing' for t in tracks):
        return 'failed', '字幕を有効にした表示だが、再生時刻に対応する字幕トラックは非表示だった。'
    return 'cant_tell', '実再生した時刻の字幕表示を特定できない。'


def assess_description(evidence):
    before, playback = evidence['before'], evidence['playback']
    if (evidence['initially_pressed'] != 'false' or evidence['pressed'] != 'true' or not playback['ended']
            or playback['error'] or not playback['visible'] or playback['height'] <= 0
            or playback['audioBytes'] <= 0 or playback['videoBytes'] <= 0
            or not before['source'] or not playback['source'] or not playback['duration']
            or not any(start < 0.1 and end >= playback['duration'] - 0.1 for start, end in playback['played'])):
        return 'cant_tell', '選択後の音声付き動画を最初から終わりまで実再生できなかった。'
    before_url, playback_url = urlsplit(before['source']), urlsplit(playback['source'])
    if (before_url.scheme, before_url.netloc, before_url.path) == (playback_url.scheme, playback_url.netloc, playback_url.path):
        return 'failed', '音声解説の選択表示が変わったが、選択前と同じ動画資源が終端まで再生された。'
    digests = evidence['resources']
    if (len(digests) == 2 and digests[0] != digests[1]
            and (before_url.scheme, before_url.netloc) == (playback_url.scheme, playback_url.netloc)):
        return 'passed', '音声解説の選択後、実データの異なる音声付き動画が終端まで再生された。解説の内容は別途確認する。'
    return 'cant_tell', '選択前後の動画資源を照合できない。'


def assess_autoplay(evidence):
    playback = evidence['playback']
    samples = evidence['samples']
    if (not evidence['before']['autoplay'] or evidence['before']['activated'] or playback['error'] or len(samples) < 2
            or samples[-1]['at'] - samples[0]['at'] <= 3000
            or samples[-1]['position'] - samples[0]['position'] <= 3
            or not all(not sample['paused'] and not sample['muted'] and sample['volume'] > 0 for sample in samples)
            or not any(sample['peak'] > 0.001 for sample in samples)):
        return 'cant_tell', '音声信号を伴う3秒超の自動再生を確認できない。'
    after = evidence['after']
    if (evidence['pause'] is not None and after and after['paused'] and not after['ended']
            and after['source'] == playback['source']):
        return 'passed', '音声の自動再生を3秒超観測し、プレーヤー自身の一時停止ボタンを操作して停止した。'
    if not playback['controls'] and evidence['scope']['plainMediaOnly']:
        return 'failed', '音声の自動再生を3秒超観測した。単一メディアと見出しだけの文書に停止や音量調整の部品がない。'
    return 'cant_tell', '音声の自動再生を確認したが、個別に止める経路や音量を調整する経路を確かめられない。'


def evaluate(criterion, plan, evidence):
    validate_plan(criterion, plan)
    assess = {
        **dict.fromkeys(TRANSCRIPT, assess_transcript),
        '1.2.2': assess_captions,
        '1.2.5': assess_description,
        '1.4.2': assess_autoplay,
    }[criterion]
    try:
        outcome, observation = assess(evidence)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        outcome, observation = 'cant_tell', 'メディアの操作結果を照合できる観測が不足している。'
    return [dict(target=plan['target'], checkpoint=f'{criterion}-01', outcome=outcome, observed=observation)]
