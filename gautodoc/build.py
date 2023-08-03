import os
import shutil
from gautodoc.common import *
from gautodoc.config import Config
from gautodoc import registry

# where the templates/ dir is, relative to this file
TEMPLATE_RELPATH = "./template"
REGISTRY_FILENAME = "./registry.json"

def get_template_abspath():
    dir_abspath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_abspath, TEMPLATE_RELPATH)

def setup_build_dir(build_abspath: str) -> str:
    """
    given gautodoc params, does various checks to make sure that the output dir
    is set up as required, and returns the abspath to place registries in.
    
    regardless of the state of everything, this should not 
    """
    if not os.path.exists(build_abspath):
        # write template for the first time
        shutil.copytree(get_template_abspath(), build_abspath)
    elif not os.path.isdir(build_abspath):
        error_exit(
            f"build dir exists but is not a directory (at {build_abspath})",
        )

    # delete any old registries
    reg_abspath = os.path.join(build_abspath, REGISTRY_FILENAME)
    if os.path.exists(reg_abspath):
        os.remove(reg_abspath)

def build(cfg: Config, dir_relpath: str):
    # set up web template
    build_abspath = os.path.abspath(os.path.join(dir_relpath, cfg.build_dir))
    setup_build_dir(build_abspath)

    # write registry
    reg = registry.load(cfg.modules, dir_relpath)
    with open(os.path.join(build_abspath, REGISTRY_FILENAME), 'w') as f:
        f.write(reg.dumps(indent=2))
