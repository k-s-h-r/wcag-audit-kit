#!/usr/bin/env python3
"""Command-line entry point for benchmarks.measurements.text_paint_probe."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.measurements import text_paint_probe

if __name__ == '__main__':
    raise SystemExit(text_paint_probe.main())
else:
    sys.modules[__name__] = text_paint_probe
