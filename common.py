"""
stuff that should be stdlib
"""

from typing import NoReturn
from dataclasses import dataclass

def error_exit(msg: str) -> NoReturn:
    """exit failure"""

    print(f"error: {msg}", file=sys.stderr)
    exit(1)

def simple(obj):
    """basically turns a class into an immutable struct"""

    return dataclass(obj, frozen=True)