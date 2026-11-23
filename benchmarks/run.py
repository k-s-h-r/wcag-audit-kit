#!/usr/bin/env python3
"""Command-line entry point for benchmarks.suite.cli."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.suite import cli

if __name__ == '__main__':
    raise SystemExit(cli.main())
else:
    sys.modules[__name__] = cli
