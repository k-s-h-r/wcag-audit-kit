"""Import path used by recorded validation scripts."""
import sys

from .suite import core

sys.modules[__name__] = core
