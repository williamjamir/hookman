import ctypes
import sys
from pathlib import Path
from zipfile import ZipFile

import attr
from attr import attrib

from hookman.exceptions import PluginNotFoundError


@attr.s(frozen=True)
class PluginInfo(object):
    """
    Class that holds all information related to the plugin with some auxiliary methods
    """
    location = attrib(type=Path)

    name = attrib(type=str, init=False)
    version = attrib(type=str, init=False)
    author = attrib(type=str, init=False)
    email = attrib(type=str, init=False)
    shared_lib_name = attrib(type=str, init=False)
    shared_lib_path = attrib(type=Path, init=False)
    description = attrib(type=str, default="Could not find a description", init=False)

    def __attrs_post_init__(self):
        plugin_config_file_content = self._load_yaml_file(self.location.read_text(encoding="utf-8"))
        object.__setattr__(self, "name", plugin_config_file_content['plugin_name'])
        object.__setattr__(self, "version", plugin_config_file_content['plugin_version'])
        object.__setattr__(self, "author", plugin_config_file_content['author'])
        object.__setattr__(self, "email", plugin_config_file_content['email'])
        object.__setattr__(self, "shared_lib_name", plugin_config_file_content['shared_lib_name'])
        object.__setattr__(self, "shared_lib_path", self.location.parent / self.shared_lib_name)

        readme_file = self.location.parent / 'readme.md'
        if readme_file.exists():
            object.__setattr__(self, "description", readme_file.read_text())

    @classmethod
    def _load_yaml_file(cls, yaml_content):
        import strictyaml
        schema = strictyaml.Map({
            "plugin_name": strictyaml.Str(),
            "plugin_version": strictyaml.Str(),
            "author": strictyaml.Str(),
            "email": strictyaml.Str(),
            "shared_lib": strictyaml.Str(),
        })
        plugin_config_file_content = strictyaml.load(yaml_content, schema).data
        if sys.platform == 'win32':
            plugin_config_file_content[
                'shared_lib_name'] = f"{plugin_config_file_content['shared_lib']}.dll"
        else:
            plugin_config_file_content[
                'shared_lib_name'] = f"lib{plugin_config_file_content['shared_lib']}.so"
        return plugin_config_file_content

    @classmethod
    def plugin_file_validation(cls, plugin_file_zip: ZipFile):
        """
        Check if the given plugin_file is valid,
        currently the only check that this method do is to verify if the shared_lib is available
        """
        list_of_files = [file.filename for file in plugin_file_zip.filelist]

        plugin_file_str = plugin_file_zip.read('plugin.yaml').decode("utf-8")
        plugin_file_content = PluginInfo._load_yaml_file(plugin_file_str)

        if plugin_file_content['shared_lib_name'] not in list_of_files:
            raise PluginNotFoundError(
                f"{plugin_file_content['shared_lib_name']} could not be found "
                f"inside the plugin file")

    @classmethod
    def is_implemented_on_plugin(cls, plugin_dll: ctypes.CDLL, hook_name: str) -> bool:
        """
        Check if the given function name is available on the plugin_dll informed

        .. note:: The hook_name should be the full name of the hook
        Ex.: {project}_{version}_{hook_name} -> hookman_v4_friction_factor
        """
        try:
            getattr(plugin_dll, hook_name)
        except AttributeError:
            return False

        return True

    @classmethod
    def get_function_address(cls, plugin_dll, hook_name):
        """
        Return the address of the requested hook for the given plugin_dll.

        .. note:: The hook_name should be the full name of the hook
        Ex.: {project}_{version}_{hook_name} -> hookman_v4_friction_factor
        """
        return ctypes.cast(getattr(plugin_dll, hook_name), ctypes.c_void_p).value
