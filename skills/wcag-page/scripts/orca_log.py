"""Index actual Orca debug speech lines by event time after the log is closed.

The producer must run with TZ=UTC. This is a transcript of Orca's output,
not an audio recording, an accessibility tree, or a WCAG judgement.
"""
import ast
from datetime import datetime, timedelta, timezone
import re


SPEECH = re.compile(
    r"^(?P<time>\d{2}:\d{2}:\d{2}\.\d{6}) - SPEECH OUTPUT: "
    r"(?P<phrase>'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")(?=[\s{]|$)"
)


def speech_in_window(log, start, end):
    """Return speech whose Orca timestamps fall in [start, end).

    Byte offsets taken while Orca is running cannot reliably delimit a step:
    the debug file buffers its writes. Read the complete closed log instead.
    """
    start = datetime.fromisoformat(start)
    end = datetime.fromisoformat(end)
    if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0):
        raise ValueError("Orca logと観察時刻はUTCで記録する")
    if not timedelta(0) < end - start < timedelta(days=1):
        raise ValueError("発話の観察窓は0秒より長く24時間未満にする")
    result = []
    for number, line in enumerate(log.splitlines(), 1):
        match = SPEECH.match(line)
        if not match:
            continue
        clock = datetime.strptime(match['time'], '%H:%M:%S.%f').time()
        candidates = [datetime.combine(start.date() + timedelta(days=delta), clock, timezone.utc)
                      for delta in (0, 1)]
        moment = next((value for value in candidates if start <= value < end), None)
        if moment is not None:
            result.append({'at': moment.isoformat(), 'line': number,
                           'phrase': ast.literal_eval(match['phrase']), 'raw': line})
    return result
