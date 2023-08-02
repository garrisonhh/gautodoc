#!/usr/bin/env python

import os
import argparse
import registry
from gconfig import Config
from gbuild import build

def gdoc_init(args):
    build_dir = os.path.relpath(args.build_dir, start=args.project_dir)

    Config(
        modules=args.modules,
        build_dir=build_dir,
    ).write(dir_relpath=args.project_dir)

def gdoc_build(args):
    cfg = Config.load(args.project_dir)
    build(cfg, args.project_dir)

def dispatch_args():
    # main parser
    gdoc_parser = argparse.ArgumentParser(
        description="a stupid simple autodoc for python",
    )
    subparsers = gdoc_parser.add_subparsers(
        required=True,
        help="gdoc subcommands",
    )

    # gdoc init
    init_parser = subparsers.add_parser(
        'init',
        help="initialize or reconfigure a gdoc project",
    )
    init_parser.set_defaults(dispatch=gdoc_init)

    init_parser.add_argument(
        'modules',
        type=str,
        nargs='+',
        help="paths to root modules to be documented",
    )
    init_parser.add_argument(
        '-d',
        '--project-dir',
        type=str,
        default='.',
        help="project directory to configure",
    )
    init_parser.add_argument(
        '-b',
        '--build-dir',
        type=str,
        default='./doc',
        help="build output directory",
    )

    # gdoc build
    build_parser = subparsers.add_parser(
        'build',
        help="build a gdoc project",
    )
    build_parser.set_defaults(dispatch=gdoc_build)

    build_parser.add_argument(
        '-d',
        '--project-dir',
        type=str,
        default='.',
        help="project directory to build",
    )

    # parse args and dispatch
    args = gdoc_parser.parse_args()
    args.dispatch(args)

if __name__ == '__main__':
    dispatch_args()