#!/usr/bin/env python3
"""Command-line entry point for benchmarks.url_runs.machine."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.url_runs import machine

if __name__ == '__main__':
    raise SystemExit(machine.main())
else:
    sys.modules[__name__] = machine
