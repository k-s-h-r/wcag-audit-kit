"""Import path used by recorded validation scripts."""
import sys

from .suite import runner

sys.modules[__name__] = runner
