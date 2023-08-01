import os
import shutil
from common import *
from gconfig import Config
import registry

# where the templates/ dir is, relative to this file
TEMPLATE_RELPATH = "./template"
# where the registries/ dir should be, relative to the build dir
REGISTRY_RELPATH = "./registries"

def get_template_abspath():
    dir_abspath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_abspath, TEMPLATE_RELPATH)

def setup_output_abspath(build_abspath: str) -> str:
    """
    given gdoc params, does various checks to make sure that the output dir
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

    # make clean gdoc folder
    out_abspath = os.path.join(build_abspath, REGISTRY_RELPATH)
    if os.path.exists(out_abspath):
        if not os.path.isdir(out_abspath):
            error_exit(
                f"output dir exists but is not a directory (at {out_abspath})",
            )

        # clear this folder
        for root, dirs, files in os.walk(out_abspath):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                shutil.rmtree(os.path.join(root, name))
    else:
        os.mkdir(out_abspath)

    return out_abspath

def build(cfg: Config, dir_relpath: str):
    # set up web template
    build_dir = os.path.abspath(os.path.join(dir_relpath, cfg.build_dir))
    registry_dir = setup_output_abspath(build_dir)
    
    # write registries
    for i, root_relpath in enumerate(cfg.modules):
        reg = registry.load(root_relpath, dir_relpath)
        
        with open(os.path.join(registry_dir, f"root{i}.json"), 'w') as f:
            f.write(reg.dumps(indent=2))