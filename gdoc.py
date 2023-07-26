#!/usr/bin/env python3
"""
a simple automatic documentation generator.
"""

import os
import sys
import shutil
# I feel a moral obligation to mention that importlib might be the absolute
# worst mess of a library I have ever seen in 10 years of programming. People
# gets paid six figures to write code like this, and for this I feel existential
# horror at the absurdity of the unfairness of the world we live in.
import importlib
from importlib import util as importlib_util
import inspect
import argparse
import html
from pprint import pprint
from dataclasses import dataclass
from typing import Optional, Iterator

def error_exit(msg):
    print(f"error: {msg}", file=sys.stderr)
    exit(1)

# module loading ===============================================================

def load_module(relpath):
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

    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

# data structures for docs =====================================================

def simple(obj):
    """basically turns a class into an immutable struct"""
    return dataclass(obj, frozen=True)

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

# doc generation ===============================================================

def get_members(obj: object) -> list[object]:
    # random stuff that appears in __dict__ for objects that I want to ignore
    BANNED = {
        '__dict__',
        '__weakref__',
    }

    def aux():
        if inspect.ismodule(obj):
            for name, val in obj.__dict__.items():
                mod = val.__module__ if hasattr(val, '__module__') else None

                if not hasattr(val, '__module__') \
                  or val.__module__ != obj.__name__:
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

# html output ==================================================================

def gen_keyword(s: str) -> str:
    return f"<span class='keyword'>{s}</span>"

def gen_ident(s: str) -> str:
    return f"<span class='ident'>{s}</span>"

def gen_type(s: str) -> str:
    return f"<span class='type'>{s}</span>"

def gen_param(param: inspect.Parameter) -> str:
    s = "<span class='param'>"

    name = f"<span class='ident param-name'>{param.name}</span>"

    if param.kind == inspect.Parameter.VAR_POSITIONAL:
        s += "*" + name
    elif param.kind == inspect.Parameter.VAR_KEYWORD:
        s += "**" + name
    else:
        s += name

        if param.annotation is not inspect.Parameter.empty:
            s += ": " + gen_type(inspect.formatannotation(param.annotation))

        if param.default is not inspect.Parameter.empty:
            s += " = " + gen_type(str(param.default))

    s += "</span>"

    return s

def gen_sig(decl: str, name: str, sig: inspect.Signature) -> str:
    s = ""

    s += f"<h2 class='decl {decl}'>"
    s += gen_keyword(decl)
    s += " "
    s += gen_ident(name)
    s += "(<span class='parameters'>"
    s += ", ".join(map(gen_param, sig.parameters.values()))
    s += "</span>)"

    if sig.return_annotation != inspect.Signature.empty:
        anno = inspect.formatannotation(sig.return_annotation)
        s += " -> " + gen_type(anno)

    s += "</h2>"

    return s

def gen_children(children: list[Entry]) -> str:
    s = ""

    s += "<div class='children'>"
    for child in children:
        s += gen_entry(child)
    s += "</div>"

    return s

def gen_entry(entry: Entry) -> str:
    s = ""

    # decl
    if isinstance(entry.meta, ModuleMeta):
        s += f"<h1 class='decl module'>{entry.name}</h1>"
    elif isinstance(entry.meta, ClassMeta):
        s += gen_sig('class', entry.name, entry.meta.sig)
    elif isinstance(entry.meta, FunctionMeta):
        s += gen_sig('def', entry.name, entry.meta.sig)

    # docstring
    if entry.docstring is not None:
        s += f"<p class='docstring'>{html.escape(entry.docstring)}</p>"

    # children
    if isinstance(entry.meta, ModuleMeta) or isinstance(entry.meta, ClassMeta):
        s += gen_children(entry.meta.children)

    return s

def gen_html(stylesheets: list[str], entries: list[Entry]) -> str:
    """generate document html"""

    s = ""
    s += "<!DOCTYPE html><html>"

    # head
    s += "<head>"
    for stylesheet in stylesheets:
        s += f"<link rel='stylesheet' " + \
             f"type='text/css' " + \
             f"href='{html.escape(stylesheet)}'>"
    s += "</head>"

    # body
    s += "<body>"
    for entry in entries:
        s += gen_entry(entry)
    s += "</body>"

    s += "</html>"

    return s

# output =======================================================================

def make_clean_dir(dirpath):
    """makes and/or cleans output directory. returns abspath"""
    dirpath = os.path.abspath(dirpath)
    shutil.rmtree(dirpath, ignore_errors=True)
    os.mkdir(dirpath)

    return dirpath

def copy_styles(dirpath, styles):
    """copies styles over to output dir, returns new relative paths"""
    copied = []
    for stylepath in styles:
        stylepath = os.path.abspath(stylepath)
        basename = os.path.basename(stylepath)
        shutil.copyfile(stylepath, os.path.join(dirpath, basename))
        copied.append(os.path.join("/", basename))

    return copied

def write_html(dirpath, html):
    with open(os.path.join(dirpath, 'index.html'), 'w') as f:
        f.write(html)    

# main =========================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="generate documentation for a module",
    )
    parser.add_argument(
        "modules",
        nargs='+',
        type=str,
        help="filepaths for the modules to be documented",
    )
    parser.add_argument(
        "-o",
        metavar="<output>",
        required=True,
        help="directory for the html output",
    )
    parser.add_argument(
        "-s",
        "--stylesheets",
        nargs='*',
        help="optional stylesheets",
    )

    return parser.parse_args()

def main():
    args = parse_args()

    # gen docs for the module
    docs = list(map(document, map(load_module, args.modules)))

    # write everything
    dirpath = make_clean_dir(args.o)
    stylesheets = copy_styles(dirpath, args.stylesheets)
    write_html(dirpath, gen_html(stylesheets, docs))

if __name__ == '__main__':
    main()