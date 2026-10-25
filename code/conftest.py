"""Puts code/common on sys.path for the tests, so `import frugalai_common` works even if the package was not
installed (`conda env create -f environment.yml` installs it in editable mode, which does the same for the
command line)."""

import sys
from pathlib import Path

_COMMON = str(Path(__file__).resolve().parent / "common")
if _COMMON not in sys.path:
    sys.path.insert(0, _COMMON)
