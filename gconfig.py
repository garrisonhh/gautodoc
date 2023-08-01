"""
dealing with reading/writing gdoc project configuration. all you need to do
to use this is create a config and write() it, or load() it from a file.
"""

from typing import Self
import os
import json
from common import *

CONFIG_FILENAME = '.gdoc'

def get_abspath(dir_relpath):
    """given relative dir, returns config filepath"""
    return os.path.abspath(os.path.join(dir_relpath, CONFIG_FILENAME))

@simple
class Config:
    modules: list[str]
    build_dir: str

    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Config):
                return vars(obj)
            return json.JSONEncoder.default(self, obj)

    def write(self, dir_relpath: str):
        with open(get_abspath(dir_relpath), 'w') as f:
            json.dump(self, f, cls=Config.Encoder, indent=2)

    @staticmethod
    def load(dir_relpath: str) -> Self:
        with open(get_abspath(dir_relpath), 'r') as f:
            return Config(**json.load(f))