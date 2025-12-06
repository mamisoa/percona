#!/usr/bin/env python3
"""
Backward-compatible shim that delegates to the packaged CLI.

This file remains so existing `python main.py` workflows keep working while the
logic lives in the `percona` package.
"""

from percona.cli import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
