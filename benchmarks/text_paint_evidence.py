"""Opt-in benchmark replay and verification for one declared text contrast target."""
from contextlib import ExitStack
import re

CHECKPOINT = '1.4.3-02'
IMAGE_BUDGET = 7
MODES = {'ai', 'full'}
DIRECTORY = 'text-paint'
SELECTOR = re.compile(r'#[a-zA-Z][\w-]*', re.ASCII)


def target(criterion, checkpoints, states):
    declared = [state for state in states if 'text_paint_target' in state]
    if not declared:
        return None
    if (criterion != '1.4.3' or CHECKPOINT not in checkpoints or len(declared) != 1
            or declared[0]['id'] != 'initial'):
        raise ValueError('文字の画素測定は1.4.3-02の初期状態に指定する')
    selector = declared[0]['text_paint_target']
    if not isinstance(selector, str) or not SELECTOR.fullmatch(selector):
        raise ValueError('文字の画素測定には単一のIDセレクターを指定する')
    return selector


def binding(meta, job, page, selector, source_digest):
    return dict(run_id=meta['run_id'], job_id=job['id'], mode=job['mode'], page=page, url=job['urls'][page],
                state='initial', checkpoint=CHECKPOINT, target=selector, source_sha256=source_digest)


def collect(run, meta, job, page, attempt):
    from . import core

    if not enabled(meta, job):
        return
    selector = target(job['criterion'], job['checkpoints'], job['states'])
    if selector is None:
        return
    source = core.local(run/'worker/public/1.4.3', page)
    frozen = core.load(run/'integrity.json')['files']
    source_digest = core.file_hash(source)
    if frozen.get(source.relative_to(run.resolve()).as_posix()) != source_digest:
        raise ValueError('文字の画素測定対象の公開ページが変更された')
    output = attempt/DIRECTORY
    receipt = binding(meta, job, page, selector, source_digest)
    try:
        from .text_paint_probe import probe
    except ImportError:
        output.mkdir()
        receipt['reason'] = '画像測定に必要なPillow又はPlaywrightが利用できない。'
    else:
        measurement = probe(source, selector, output, IMAGE_BUDGET)
        if measurement['source_sha256'] != source_digest:
            raise ValueError('文字の画素測定中に公開ページが変更された')
    core.save(output/'receipt.json', receipt)


def enabled(meta, job):
    return (meta.get('configuration', {}).get('text_paint_images') == IMAGE_BUDGET
            and job['mode'] in MODES and job['criterion'] == '1.4.3')


def remeasure(run, output, measurement, frozen):
    """Recalculate the result from the fixed seven frames rather than trusting their reported verdict."""
    from . import core
    from .text_paint_probe import CAPTURE_STAGES, Held, RESULT_SCOPE, RGB, VIEWPORT, analyze_frames
    from PIL import Image

    frames = measurement.get('frames')
    region = measurement.get('range_css_px')
    size = measurement.get('font_css_px')
    weight = measurement.get('font_weight')
    if (measurement.get('status') != 'measured' or measurement.get('scope') != RESULT_SCOPE
            or measurement.get('blocked_requests') != [] or measurement.get('image_limit') != IMAGE_BUDGET
            or measurement.get('viewport_css_px') != list(VIEWPORT.values()) or measurement.get('scroll_css_px') != [0, 0]
            or not isinstance(measurement.get('browser'), str) or not measurement['browser']
            or not isinstance(frames, dict) or set(frames) != set(CAPTURE_STAGES)
            or not isinstance(region, list) or len(region) != 4 or not all(core.css_number(v) for v in region)
            or not core.css_number(size) or size <= 0 or type(weight) is not int or not 1 <= weight <= 1000):
        return None
    x, y, width, height = region
    if min(x, y) < 2 or min(width, height) <= 0 or x + width + 2 > VIEWPORT['width'] or y + height + 2 > VIEWPORT['height']:
        return None
    original = frames['original']
    fill = original.get('fill') if isinstance(original, dict) else None
    if not isinstance(fill, str) or not RGB.fullmatch(fill) or any(int(v) > 255 for v in RGB.fullmatch(fill).groups()):
        return None
    first = dict(rangeRects=[region], fill=fill, font=[f'{size}px', str(weight)])
    images, paths = {}, []
    try:
        with ExitStack() as opened:
            for stage, color in CAPTURE_STAGES.items():
                item = frames[stage]
                filename = f'{stage}.png'
                path = core.local(output, filename)
                relative = path.relative_to(run).as_posix()
                expected = frozen.get(relative)
                if (path != output/filename or not isinstance(item, dict) or item.get('path') != filename
                        or not expected or item.get('sha256') != expected or core.file_hash(path) != expected
                        or item.get('fill') != (fill if color is None else color)):
                    return None
                image = opened.enter_context(Image.open(path))
                if image.format != 'PNG' or image.size != tuple(VIEWPORT.values()):
                    return None
                images[stage] = image
                paths.append(relative)
            recomputed = analyze_frames(images, first)
    except (Held, KeyError, OSError, TypeError, ValueError, Image.DecompressionBombError):
        return None
    fields = ('ratio', 'threshold', 'foreground', 'background', 'font_css_px', 'font_weight')
    if (recomputed['status'] != 'measured' or any(measurement.get(field) != recomputed[field] for field in fields)
            or measurement.get('threshold_met') is not recomputed['threshold_met']):
        return None
    return recomputed, paths


def predictions(run, meta, job, progress, frozen):
    from . import core

    if not enabled(meta, job):
        return {}
    selector = target(job['criterion'], job['checkpoints'], job['states'])
    if selector is None:
        return {}
    result = {}
    for page in job['pages']:
        try:
            attempt, job_receipt = core.completed_attempt(run, job, progress, page, frozen)
        except (KeyError, TypeError, ValueError):
            continue
        if attempt is None:
            continue
        source = core.local(run/'worker/public/1.4.3', page)
        source_digest = frozen.get(source.relative_to(run).as_posix())
        output = attempt.parent/DIRECTORY
        receipt_path = output/'receipt.json'
        if receipt_path.resolve() != receipt_path:
            continue
        receipt = core.read_frozen(run, receipt_path, frozen)
        if not source_digest or not receipt or any(
            receipt.get(key) != value for key, value in binding(meta, job, page, selector, source_digest).items()
        ):
            continue
        proof = [path.relative_to(run).as_posix() for path in (job_receipt, receipt_path)]
        reason = receipt.get('reason')
        row = dict(page=page, state='initial', target=selector, checkpoint=CHECKPOINT, outcome='cant_tell', method='program',
                   observed=reason if isinstance(reason, str) else '固定したページと画素の測定結果を照合できない。',
                   source='isolated Chromium / text paint', evidence=proof)
        result[core.observation_key(row)] = row
        measurement_path = output/'result.json'
        if measurement_path.resolve() != measurement_path:
            continue
        measurement = core.read_frozen(run, measurement_path, frozen)
        if (not measurement or measurement.get('target') != selector or measurement.get('source') != source.name
                or measurement.get('source_sha256') != source_digest):
            continue
        proof.append(measurement_path.relative_to(run).as_posix())
        if measurement.get('status') == 'hold':
            reason = measurement.get('reason')
            row['observed'] = '文字の画素測定を確定できない。' + (reason if isinstance(reason, str) else '')
            continue
        try:
            verified = remeasure(run, output, measurement, frozen)
        except ImportError:
            row['observed'] = '画像証拠の再計算に必要なPillow又はPlaywrightが利用できない。'
            continue
        if verified is not None:
            observed, paths = verified
            proof.extend(paths)
            row.update(outcome='passed' if observed['threshold_met'] else 'failed',
                       observed=f'画素の実測比 {observed["ratio"]!r}:1、比較基準 {observed["threshold"]:g}:1。'
                       f'前景 {observed["foreground"]}、背景 {observed["background"]}、'
                       f'文字 {observed["font_css_px"]:g} CSS px、太さ {observed["font_weight"]}。')
    return result
