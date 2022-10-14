#!python3.10
# -*- coding: utf-8 -*-
"""env.py

Script for setting up the environment for using test_shuf.py.
"""

import os
import sys
from pathlib import Path


def activate_venv() -> bool:
    """Activate the venv in current directory, creating if necessary."""
    for path in Path.cwd().iterdir():
        if path.is_dir() and path.name.endswith("env"):
            activate_path = path / "bin/activate"
            if os.system(f"source {activate_path}") == 0:
                break
            return False
    else:
        if os.system(f"{sys.executable} -m venv .venv") == 0:
            if os.system("source .venv/bin/activate") != 0:
                print("FAILED to activate virtual environment, aborted.")
                return False
        else:
            print("FAILED to create virtual environment, aborted.")
            return False
    return True


def install_rich() -> bool:
    """Install the rich library after venv is activated."""
    if os.system("python -m pip install rich") == 0:
        return True
    print("FAILED to install the rich library, aborted.")
    return False


def main() -> None:
    """Main driver function."""
    if activate_venv():
        install_rich()


if __name__ == "__main__":
    main()
