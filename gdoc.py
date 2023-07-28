#!/usr/bin/env python
"""
a simple automatic documentation generator.
"""

import os
import sys
import shutil
import inspect
import argparse
import html
from pprint import pprint
import analysis
from common import *

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

def gen_children(children: list[analysis.Entry]) -> str:
    s = ""

    s += "<div class='children'>"
    for child in children:
        s += gen_entry(child)
    s += "</div>"

    return s

def gen_entry(entry: analysis.Entry) -> str:
    s = ""

    # decl
    if isinstance(entry.meta, analysis.ModuleMeta):
        s += f"<h1 class='decl module'>{entry.name}</h1>"
    elif isinstance(entry.meta, analysis.ClassMeta):
        s += gen_sig('class', entry.name, entry.meta.sig)
    elif isinstance(entry.meta, analysis.FunctionMeta):
        s += gen_sig('def', entry.name, entry.meta.sig)

    # docstring
    if entry.docstring is not None:
        s += f"<p class='docstring'>{html.escape(entry.docstring)}</p>"

    # children
    if isinstance(entry.meta, analysis.ModuleMeta) \
        or isinstance(entry.meta, analysis.ClassMeta):
        s += gen_children(entry.meta.children)

    return s

def gen_html(stylesheets: list[str], entries: list[analysis.Entry]) -> str:
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
    docs = list(map(analysis.analyze, args.modules))

    # write everything
    dirpath = make_clean_dir(args.o)
    stylesheets = copy_styles(dirpath, args.stylesheets)
    write_html(dirpath, gen_html(stylesheets, docs))

if __name__ == '__main__':
    main()