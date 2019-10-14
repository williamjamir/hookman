import ctypes
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import List, Union


def find_config_files(plugin_dirs: Union[List[Path], Path]) -> List[Path]:
    """
    Try to find all configurations files from plugins implementations on the given path (plugins_dirs)
    If in the given there is any plugin, this function will return None
    """
    config_files = []

    if not isinstance(plugin_dirs, list):
        plugin_dirs = [plugin_dirs]

    for plugin_dir in plugin_dirs:
        config_files += plugin_dir.glob("**/plugin.yaml")

    return config_files


@contextmanager
def change_path_env(shared_lib_path: str):
    """
    Change PATH environment adding the shared library path to it.
    """
    old_path = os.environ["PATH"]
    if sys.platform.startswith("win"):
        os.environ["PATH"] = old_path + os.pathsep + os.path.dirname(shared_lib_path)
    try:
        yield
    finally:
        os.environ["PATH"] = old_path


@contextmanager
def load_shared_lib(shared_lib_path: str) -> ctypes.CDLL:
    """
    Load a shared library using ctypes freeing the resource at end.
    """
    with change_path_env(shared_lib_path):
        plugin_dll = ctypes.cdll.LoadLibrary(shared_lib_path)

    try:
        yield plugin_dll
    finally:
        if sys.platform == "win32":
            from _ctypes import FreeLibrary

            FreeLibrary(plugin_dll._handle)
        else:
            from _ctypes import dlclose

            dlclose(plugin_dll._handle)
