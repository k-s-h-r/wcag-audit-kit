#!/usr/bin/env python3
"""Command-line entry point for benchmarks.url_runs.exploration."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.url_runs import exploration

if __name__ == '__main__':
    raise SystemExit(exploration.main())
else:
    sys.modules[__name__] = exploration
