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
                    config_yaml = yaml.load(config_file.read(), yaml.Loader) or {}
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

    def package(self, name: str) -> list:
        """Return list of files in package having `name` (processing includes)."""
        # # FIXME: return the package config (not only files), factorizing here some logic from package.push()
        # package_config = self.config.package(name)
        # files = package_config.get('files', [])  # make_filenames
        # files_to_run = package_config.get('run', [])  # make_filename_relative
        # reset = package_config.get('reset', False)
        package_files = []
        if self.config_filename == None:
            raise AssertionError('Packages not available when no config file')
        try:
            package_config = self.config.get('packages', {})[name]
        except KeyError as e:
            raise ValueError(f"Package not found: {name}  - packages available: {', '.join(self.config.get('packages', {}).keys())}")

        for file_description in package_config.get('files', []):
            package_files += self.make_filenames(file_description)

        for package_to_include in package_config.get('include', []):
            try:
                package_files = self.package(package_to_include) + package_files
            except ValueError as e:
                raise KeyError(f'{e} - while including in: {name}')

        return package_files

    def make_filenames(self, file_description):
        """Return a list of tuples (source, destination) from `file_description`."""
        if not (type(file_description) is str or (type(file_description) in [list, tuple, set] and len(file_description) == 2)):
            raise ValueError(f"File definition must be string or list, eg. 'source.py' or ['source.py', 'destination.py'] (got {file_description})")
        filenames = []
        source, destination = [file_description, None] if type(file_description) is str else file_description
        source_relative = self.make_filename_relative(source)
        if '*' not in source_relative:
            # FIXME: if destination is a directory (ends with /), join destination directory and source filename
            # filenames.append((source_relative, destination or source))
            filenames.append((source_relative, self.make_filename_destination(source, destination)))
        else:
            for source_file in glob.iglob(source_relative, recursive=True):  # Note: allow wildcards in source files, eg. 'tests/*.py' or 'tests/**/*.py``
                if os.path.isdir(source_file):
                    continue  # Note: ignore directories: they are created by `device.put()`.
                if destination is not None:
                    # destination_file = destination
                    destination_file = self.make_filename_destination(source_file, destination)
                else:
                    # Note: make destination_file = source_file without relative path prefix
                    relative_path = os.path.dirname(self.config_filename)
                    destination_file = source_file[1+len(relative_path):]
                filenames.append((source_file, destination_file))
        return filenames

    def make_filename_relative(self, filename):
        """Return `filename` made relative to config file path."""
        return os.path.relpath(os.path.join(
                os.path.relpath(os.path.dirname(self.config_filename or './')),
                filename))

    def make_filename_destination(self, source_description, destination_description):
        """Return the destination path and filename, according the rules."""
        if destination_description is None:
            return source_description
        elif destination_description.endswith('/'):
            return os.path.join(os.path.dirname(destination_description), os.path.basename(source_description))
        else:
            return destination_description


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
