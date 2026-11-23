#!/usr/bin/env python3
"""Command-line entry point for benchmarks.measurements.inactive_control_probe."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.measurements import inactive_control_probe

if __name__ == '__main__':
    raise SystemExit(inactive_control_probe.main())
else:
    sys.modules[__name__] = inactive_control_probe
