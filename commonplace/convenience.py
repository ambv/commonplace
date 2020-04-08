"""Almost one liners. But handy."""

from __future__ import annotations
from typing import *

from pathlib import Path


def find_dot_env(directory: Path) -> Optional[Path]:
    if not directory.is_dir():
        return None

    while True:
        maybe_result = directory / ".env"
        if maybe_result.is_file():
            return maybe_result

        if directory.root == directory:
            # we are at the root, we failed
            return None

        directory = directory.parent
