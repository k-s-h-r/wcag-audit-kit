#!/usr/bin/env python3
"""Command-line entry point for benchmarks.measurements.native_status."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.measurements import native_status

if __name__ == '__main__':
    raise SystemExit(native_status.main())
else:
    sys.modules[__name__] = native_status
