"""Import path used by recorded validation scripts."""
import sys

from .url_runs import scoring

sys.modules[__name__] = scoring
