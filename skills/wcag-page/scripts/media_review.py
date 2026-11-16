"""Validate interval bookkeeping, without asserting that content was understood."""
import math


def number(value):
    return type(value) in {int, float} and math.isfinite(value)


def validate_review(value, complete):
    if not isinstance(value, dict) or not isinstance(value.get('source'), str) or not value['source'].strip():
        raise ValueError('media_reviewには実際のsourceが必要')
    if value.get('timeline') not in {'prerecorded', 'live_window'}:
        raise ValueError('media_reviewのtimelineはprerecorded又はlive_window')
    window = value.get('window_description')
    if value['timeline'] == 'live_window' and (not isinstance(window,str) or len(window.strip()) < 10):
        raise ValueError('ライブは実際に観察した期間と範囲を明記する')
    duration = value.get('duration')
    if not number(duration) or duration <= 0:
        raise ValueError('媒体の全長又は観察窓のdurationが必要')
    if not isinstance(value.get('comparison'),str) or len(value['comparison'].strip()) < 10:
        raise ValueError('何と何の情報を比較したかを具体化する')
    intervals = value.get('intervals')
    if not isinstance(intervals, list) or not intervals:
        raise ValueError('比較した区間と残る区間をintervalsへ記録する')
    covered = []
    evidence = []
    unreviewed = False
    for interval in intervals:
        if not isinstance(interval, dict):
            raise ValueError('各区間はobjectにする')
        start, end = interval.get('start'), interval.get('end')
        if not number(start) or not number(end) or start < 0 or end <= start or end > duration + 1e-6:
            raise ValueError('区間のstart/endが媒体の範囲外又は不正')
        if interval.get('status') == 'reviewed':
            for key in ['observed', 'expected']:
                if not isinstance(interval.get(key), str) or len(interval[key].strip()) < 10:
                    raise ValueError('各区間に実際の情報と期待結果を具体的に記録する')
            proof = interval.get('evidence')
            if not isinstance(proof, list) or not proof or any(not isinstance(path, str) or not path.strip() for path in proof):
                raise ValueError('比較した各区間に証拠が必要')
            evidence.extend(proof)
            covered.append((start, end))
        elif interval.get('status') == 'not_reviewed':
            unreviewed = True
            if not isinstance(interval.get('reason'), str) or len(interval['reason'].strip()) < 10:
                raise ValueError('未確認区間には不足する観察を具体的に記す')
        else:
            raise ValueError('区間のstatusはreviewed又はnot_reviewed')
    if complete:
        if unreviewed:
            raise ValueError('未確認の媒体区間があるため全対象を検証済みにできない')
        end = 0.0
        for start, stop in sorted(covered):
            if start > end + 1e-6:
                raise ValueError('媒体の比較区間に抜けがある')
            end = max(end, stop)
        if end < duration - 1e-6:
            raise ValueError('媒体の末尾まで比較していない')
    return evidence
