"""
dealing with reading/writing gautodoc project configuration. all you need to do
to use this is create a config and write() it, or load() it from a file.
"""

from typing import Self
import os
import json
from gautodoc.common import *

CONFIG_FILENAME = '.gautodoc'

def get_abspath(dir_relpath):
    """given relative dir, returns config filepath"""
    return os.path.abspath(os.path.join(dir_relpath, CONFIG_FILENAME))

@simple
class Config:
    """record of configuration details for a documented project"""

    modules: list[str]
    build_dir: str

    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Config):
                return vars(obj)
            return json.JSONEncoder.default(self, obj)

    @staticmethod
    def load(dir_relpath: str) -> Self:
        """loads a project's configuration"""
        try:
            with open(get_abspath(dir_relpath), 'r') as f:
                return Config(**json.load(f))
        except FileNotFoundException as e:
            error_exit(
                f"failed to find {CONFIG_FILENAME} in {dir_relpath} :(\n" + \
                f"did you forget to run `gautodoc init`?"
            )

    def write(self, dir_relpath: str):
        """writes configuration to the correct file"""
        with open(get_abspath(dir_relpath), 'w') as f:
            json.dump(self, f, cls=Config.Encoder, indent=2)