from StcIntPythonPL import *
import json
import os


def get_version(package_path):
    # Initialize info before loading
    info = {}
    file_path = os.path.join(package_path, 'version.json')
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            buf = f.read()
        assert buf is not None
        info = json.loads(buf)
        if not isinstance(info, dict):
            info = {}
    if "version" not in info:
        info["version"] = "UNKNOWN"
    if "dependencies" not in info:
        info["dependencies"] = {}
    return info


def get_stak_core_version():
    stc_sys = CStcSystem.Instance()
    cdp = stc_sys.GetApplicationCommonDataPath()
    pkg_path = os.path.join(cdp, 'STAKCommands', 'spirent', 'core')
    return get_version(pkg_path)
