"""Executable module entrypoint for python -m logo2svg."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
