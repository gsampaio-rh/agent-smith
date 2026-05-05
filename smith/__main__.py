"""Allow running as `python -m smith`."""

import sys

from smith.cli import main

sys.exit(main())
