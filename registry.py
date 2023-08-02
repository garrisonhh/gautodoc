"""
loading python modules and packages intuitively
"""

from typing import Self, Optional
from common import *
import sys
import os
import json
import inspect
from inspect import Signature, Parameter
from importlib import util as importlib_util

# inspecting these on classes/modules breaks stuff
BANNED_MEMBERS = {
    '__builtin__',
    '__dict__',
    '__weakref__',
}

@simple
class Function:
    name: str
    sig: Signature
    doc: Optional[str]

@simple
class Class:
    name: str
    sig: Signature
    doc: Optional[str]

    classes: list[Self]
    functions: list[Function]

@simple
class Module:
    name: str
    abspath: str
    package: Optional[str] # 'none' for root
    doc: Optional[str]

    classes: list[Class]
    functions: list[Function]

@simple
class Registry:
    abspath: str
    modules: list[Module]

    class Encoder(json.JSONEncoder):
        def default(self, obj):
            # simple classes can just use vars()
            simple = [Function, Class, Module, Registry]
            for c in simple:
                if isinstance(obj, c):
                    return vars(obj)

            # signatures and signature-related objects need some processing
            if isinstance(obj, Signature):
                returns = None
                if obj.return_annotation != Signature.empty:
                    returns = inspect.formatannotation(obj.return_annotation)

                return {
                    "params": list(obj.parameters.values()),
                    "returns": returns,
                }
            elif isinstance(obj, Parameter):
                anno = None
                if obj.annotation != Parameter.empty:
                    anno = inspect.formatannotation(obj.annotation)

                return {
                    "name": obj.name,
                    "kind": str(obj.kind).lower(),
                    "anno": anno 
                }

            # leave everything else default
            return json.JSONEncoder.default(self, obj)

    def dumps(self, **kwargs):
        """dump this registry to json with args passed through"""
        return json.dumps(self, cls=Registry.Encoder, **kwargs)

def getdoc(x) -> Optional[str]:
    return x.__doc__ if hasattr(x, '__doc__') else None

def getmodule(x):
    """useful for pruning out stuff that isn't from the same module"""
    if inspect.ismodule(x):
        return x
    elif hasattr(x, '__module__'):
        return sys.modules[x.__module__]
    return None

def should_document_member(name, obj, mod, pred=None):
    """helper for member doc functions"""
    if name in BANNED_MEMBERS:
        return False
    elif pred and not pred(obj):
        return False
    elif hasattr(obj, '__module__'):
        return sys.modules[obj.__module__] is mod

    return False

def document_member_functions(x) -> list[Function]:
    within = getmodule(x)

    funcs = []
    for name, obj in vars(x).items():
        if should_document_member(name, obj, within, inspect.isfunction):
            funcs.append(document_function(name, obj))

    return funcs

def document_member_classes(x) -> list[Class]:
    within = getmodule(x)

    classes = []
    for name, obj in vars(x).items():
        if should_document_member(name, obj, within, inspect.isclass):
            classes.append(document_class(within, name, obj))

    return classes

def document_function(name: str, f) -> Function:
    return Function(
        name=name,
        sig=inspect.signature(f),
        doc=getdoc(f),
    )

def document_class(within, name: str, c) -> Class:
    return Class(
        name=name,
        sig=inspect.signature(c),
        doc=getdoc(c),
        classes=document_member_classes(c),
        functions=document_member_functions(c),
    )

def document_module(mod) -> Module:
    """loads a module from its __dict__"""
    return Module(
        name=mod.__name__,
        abspath=os.path.abspath(mod.__file__),
        package=mod.__package__ or None,
        doc=getdoc(mod),
        classes=document_member_classes(mod),
        functions=document_member_functions(mod),
    )

def referenced_modules(mod) -> list:
    """get imported modules of a module dict"""
    modules = set()
    for obj in vars(mod).values():
        got = getmodule(obj)
        if got:
            modules.add(got)

    return list(modules)

def load_module(name: str, abspath: str):
    spec = importlib_util.spec_from_file_location(name, abspath)
    module = importlib_util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    return module

def find_modules(
    root_abspaths: list[str],
    project_abspath: str
) -> list[Module]:
    assert len(root_abspaths) > 0

    queue = []
    seen = set()
    mods = []

    # setup input modules
    for root_abspath in root_abspaths:
        mod_name, _ = os.path.splitext(os.path.basename(root_abspath))
        queue.append(load_module(mod_name, root_abspath))

    # comb through modules and load
    while len(queue) > 0:
        # ensure it has a file (only untrue for specific python stdlib modules)
        obj = queue.pop()
        if not hasattr(obj, "__file__"):
            continue

        # check if this module has been seen already
        if obj in seen:
            continue
        else:
            seen.add(obj)

        # check if this module is part of the project
        abspath = os.path.abspath(obj.__file__)
        if not abspath.startswith(project_abspath):
            continue

        # store this module and add its references to the queue
        mods.append(document_module(obj))
        queue += referenced_modules(obj)

    return mods

def load(root_relpaths: list[str], project_relpath: str) -> Registry:
    """
    load a root module and all of the submodules in the project that the root
    module references

    if project_relpath is None, project_relpath will be set to the folder that
    root_relpath is located in
    """
    root_abspaths = list(map(os.path.abspath, root_relpaths))
    project_abspath = os.path.abspath(project_relpath)
    modules = find_modules(root_relpaths, project_abspath)

    return Registry(
        abspath=project_abspath,
        modules=modules,
    )