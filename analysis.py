from typing import Optional
from common import *
import os
import sys
import inspect
# I feel a moral obligation to mention that importlib might be the absolute
# worst mess of a library I have ever seen in 10 years of programming. People
# gets paid six figures to write code like this, and for this I feel existential
# horror at the absurdity of the unfairness of the world we live in.
import importlib
# this fixes annoying bullshit with this stupid fucking library. fuck you. who
# the fuck wrote this library again? who reviewed this shit and merged it?
from importlib import util as importlib_util

# TODO I have discovered 'runpy.run_path' which is a MUCH better alternative
# than using importlib, I think

# importing ====================================================================

def load_module(relpath: str):
    """programmatically loads a module for doc generation from a path."""

    abspath = os.path.abspath(relpath)

    # ensure directory is in sys.path
    dirpath = os.path.dirname(abspath)
    sys.path.insert(0, dirpath)

    # get importlib spec
    name = os.path.splitext(os.path.basename(abspath))[0]
    spec = importlib_util.find_spec(name)

    # if module doesn't exist, instead of throwing a reasonable error, this
    # does the **UNDOCUMENTED** behavior of returning None
    if spec is None:
        error_exit(f"could not load module at {abspath}")

    # why the fuck would you ever design a library this way? this is like
    # actually written by someone with brain damage. and an expensive college
    # degree they didn't deserve.
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

# documenting ==================================================================

@simple
class ModuleMeta:
    children: list

@simple
class ClassMeta:
    sig: inspect.Signature
    children: list

@simple
class FunctionMeta:
    sig: inspect.Signature

Meta = ModuleMeta | ClassMeta | FunctionMeta

@simple
class Entry:
    """documentation for some object"""

    name: str
    docstring: Optional[str]
    meta: Meta

def get_members(obj: object) -> list[object]:
    # random stuff that appears in __dict__ for objects that I want to ignore
    BANNED = {
        '__dict__',
        '__weakref__',
    }

    def aux():
        if inspect.ismodule(obj):
            for name, val in obj.__dict__.items():
                is_module_decl = hasattr(val, '__module__')

                if not is_module_decl or val.__module__ != obj.__name__:
                    # this value wasn't defined in this module
                    continue

                yield val
        else:
            for name, val in obj.__dict__.items():
                if name in BANNED:
                    continue

                yield val

    return list(aux())

def document_all(objs: list[object]) -> list[Entry]:
    return list(filter(lambda x: x, map(document, objs)))

def document(obj: object) -> Optional[Entry]:
    """attempt to generate documentation for some object"""

    # check if this should be documented, create metadata if so
    meta = None

    if inspect.ismodule(obj):
        children = document_all(get_members(obj))
        meta = ModuleMeta(children)
    elif inspect.isclass(obj):
        sig = inspect.signature(obj)
        children = document_all(get_members(obj))
        meta = ClassMeta(sig, children)
    elif inspect.isfunction(obj):
        sig = inspect.signature(obj)
        meta = FunctionMeta(sig)
    else:
        # undocumentable
        return None

    # get other entry attrs
    name = obj.__name__
    docstring = inspect.getdoc(obj)

    return Entry(name, docstring, meta)

# pipes ========================================================================

def analyze(relpath: str) -> Optional[Entry]:
    return document(load_module(relpath))
