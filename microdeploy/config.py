"""
Microdeploy Configuration manager.
"""

import yaml
import glob
import re
import os


class Config(object):

    # config = None

    def __init__(self, config_filename=None, default_baudrate=115200, override={}):

        if config_filename:
            try:
                with open(config_filename) as config_file:
                    config_yaml = yaml.load(config_file.read(), yaml.Loader)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Config file not found: '{config_filename}'")
            except yaml.scanner.ScannerError as e:
                message = str(f'\t{e}').replace('\n', '\n\t')  # indent message from ScannerError
                raise yaml.scanner.ScannerError(f"Error in config file: {config_filename}\n\n{message}")
        else:
            config_file = None
            config_yaml = {}

        self.config = {
            'packages': config_yaml.get('packages', {}),
            'device': config_yaml.get('device', {}),
            'default': {
                # 'destination': config_yaml.get('default', {}).get('destination') or '/' or None,  # default path of destination for put files to MCU
                'baudrate': config_yaml.get('default', {}).get('baudrate') or default_baudrate}}

        dict_update(self.config, override)
        self.config_filename = config_filename

    def device(self) -> dict:
        """Return device configuration, applying `*overrides`."""
        device = self.config.get('device', {})
        device = dict(device)
        return {
            'port': device.get('port'),
            'baudrate': device.get('baudrate', self.config['default']['baudrate'])}

    def package(self, name: str) -> dict:
        """Return package configuration dict."""
        try:
            package = self.config.get('packages', {})[name]
        except KeyError as e:
            KeyError(f"Package not found: {name}  - packages available: {', '.join(self.config.get('packages', {}).keys())}")

        try:
            ignore = set()
            for package_to_include in package.get('include', []):
                to_ignore = self.config.get('packages', {})[package_to_include].get('ignore', [])
                if to_ignore:
                    ignore.update(to_ignore)
                    package['ignore'] = list(ignore)
        except KeyError as e:
            raise KeyError(f'Package not found: {package_to_include} - in {name}.include')

        return package

    def package_files(self, name: str) -> list:
        """Return list of files in package having `name` (processing includes)."""
        try:
            package_config = self.package(name)
        except KeyError as e:
            raise ValueError(f"Package not found: {name}  - packages available: {', '.join(self.config.get('packages', {}).keys())}")

        def ignore(filename):
            return any(re.search(ignored, filename) for ignored in package_config.get('ignore', []))

        package_files = []
        for file_desc in package_config.get('files', []):
            if type(file_desc) is not str and not len(file_desc) == 2:
                raise ValueError("File definition must be string or tuple, eg. 'main.py' or ('source.py', 'destination.py')")
            source, destination = [file_desc, None] if type(file_desc) is str else file_desc
            source_relative = self.make_relative_to_configfile(source)
            if ignore(source_relative):
                continue
            if '*' not in source_relative:
                package_files.append((source_relative, destination or source))
            else:
                for source_file in glob.iglob(source_relative, recursive=True):  # Note: this allows wildcards in source files, eg. 'tests/*.py' or 'tests/**/*.py``
                    if os.path.isdir(source_file):
                        continue
                    if ignore(source_file):
                        continue
                    if destination is not None:
                        destination_file = destination
                    else:
                        relative_path = os.path.relpath(os.path.dirname(self.config_filename) or '.')
                        destination_file = source_file[1+len(relative_path):]
                    package_files.append((source_file, destination_file))

        for package_to_include in package_config.get('include', []):
            try:
                package_files = self.package_files(package_to_include) + package_files
            except ValueError as e:
                raise KeyError(f'Package not found: {package_to_include} - in {name}.include')

        return package_files

    def make_relative_to_configfile(self, filename):
        """Return `filename` made relative to config file path."""
        return os.path.join(os.path.relpath(os.path.dirname(self.config_filename) or '.'), filename)

class Configurable(object):
    """
    Abstract class base for components (ie. device, package).
    """
    def __init__(self, config: Config):
        self.config = config


# Helpers

def dict_update(d1, d2):
    """
    Update `d1` with `d2` deeply.
    """
    for k in d2:
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
            dict_update(d1[k], d2[k])
        else:
            d1[k] = d2[k]
