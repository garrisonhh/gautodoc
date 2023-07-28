"""
loading python modules and packages intuitively
"""

from typing import Self, Optional
from common import *
import os
import runpy
import inspect
from inspect import Signature, Parameter
import json

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
                    "params": list(obj.parameters.items()),
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
    """gets docstring from both modules dicts and objects"""
    return x.__doc__ if hasattr(x, '__doc__') else None

def document_function(name: str, f) -> Function:
    return Function(
        name=name,
        sig=inspect.signature(f),
        doc=getdoc(f),
    )

def document_member_functions(d: dict) -> list[Function]:
    funcs = []
    for name, obj in d.items():
        if name not in BANNED_MEMBERS and inspect.isfunction(obj):
            funcs.append(document_function(name, obj))

    return funcs

def document_class(name: str, c) -> Class:
    return Class(
        name=name,
        sig=inspect.signature(c),
        doc=getdoc(c),
        classes=document_member_classes(c.__dict__),
        functions=document_member_functions(c.__dict__),
    )

def document_member_classes(d: dict) -> list[Class]:
    classes = []
    for name, obj in d.items():
        if name not in BANNED_MEMBERS and inspect.isclass(obj):
            classes.append(document_class(name, obj))

    return classes

def document_module(abspath: str, data: dict) -> Module:
    """loads a module from its __dict__"""
    return Module(
        name=data["__name__"],
        abspath=abspath,
        package=data["__package__"] or None,
        doc=getdoc(data),
        classes=document_member_classes(data),
        functions=document_member_functions(data),
    )

def referenced_modules(mod: dict) -> list:
    """get imported modules of a module dict"""
    modules = set()
    for k, obj in mod.items():
        if inspect.ismodule(obj):
            # direct import
            modules.add(obj)
        elif inspect.isfunction(obj):
            # detects 'from x import *'
            guess = inspect.getmodule(obj)
            if guess:
                modules.add(guess)

    return list(modules)

def find_modules(root_name: str, root_abspath: str) -> list[Module]:
    # set up root module
    data = runpy.run_path(root_abspath)
    data["__name__"] = root_name

    # comb through modules and load
    queue = referenced_modules(data)
    known = set(root_abspath)
    mods = [document_module(root_abspath, data)]

    root_dir = os.path.dirname(root_abspath)

    while len(queue) > 0:
        # ensure it has a file (only untrue for specific python stdlib modules)
        obj = queue.pop()
        if not hasattr(obj, "__file__"):
            continue

        # check if this module has been seen already
        abspath = os.path.abspath(obj.__file__)
        if abspath in known:
            continue

        known.add(abspath)

        # check if this module is part of the project
        if not abspath.startswith(root_dir):
            continue

        # store this module and add its references to the queue
        data = obj.__dict__
        mods.append(document_module(abspath, data))
        queue += referenced_modules(data)

    return mods

def load(root_relpath: str, project_relpath: Optional[str] = None) -> Registry:
    """
    load a root module and all of the submodules in the project that the root
    module references

    if project_relpath is None, project_relpath will be set to the folder that
    root_relpath is located in
    """
    # reshape paths
    root_abspath = os.path.abspath(root_relpath)

    if not project_relpath:
        project_abspath = os.path.dirname(root_abspath)
    else:
        project_abspath = os.path.abspath(project_relpath)

    root_name, _ = os.path.splitext(os.path.basename(root_abspath))

    # find and register modules
    modules = find_modules(root_name, root_abspath)

    return Registry(
        abspath=project_abspath,
        modules=modules,
    )

# TODO remove
from pprint import pprint
if __name__ == '__main__':
    reg = load("./gdoc.py")
    print(reg.dumps(indent=2))