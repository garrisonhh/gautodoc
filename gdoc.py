#!/usr/bin/env python
"""
a simple automatic documentation generator.
"""

import argparse
import registry

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
        "--output",
        metavar="<output>",
        required=True,
        help="directory for the html output",
    )

    return parser.parse_args()

def main():
    args = parse_args()
    docs = list(map(analysis.analyze, args.modules))

if __name__ == '__main__':
    main()