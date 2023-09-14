"""
Microdeploy.

Deploy micropython projects on MCU.

Purpose: Provide a simple and configurable toolkit for deploying projects on MCU.
The config file `deploy.yaml` can exist at the root of the project and define packages of files to upload to MCU,
enabling to deploy parts of your project (eg. production, unittests and development).

This deployment toolkit has become a complete support for working with your MCU:
filesystem acces, package upload with caching, serial console (and TODO: firmware flashing).

This tool can be used as CLI or API.

  - CLI Usage: `python -m deploy`

  - API Usage: `help(Microdeploy)`

TODO:
  - Progressbar in `device.put()`: Factorize callback format in device.put() and package.push(): calls to `_progress()` must return a `dict` and the string must be generated in class `Microdeploy`.
  - Add feature: erase and flash firmware
"""

from . import config as config_module
from . import device as device_module
from . import package as package_module
from inspect import signature as inspect_signature
import sys


class Microdeploy(object):
    """
    MCU deployment facade for CLI  - see file `__main__.py`.
    
    Also words as regular python package:

        import microdeploy
        deploy = Microdeploy()
        deploy.device.ls()
        deploy.package.put('tests')

        Microdeploy(config='deploy.yaml')
        Microdeploy(config='deploy.yaml').device
        Microdeploy(config='deploy.yaml').device.ls()
        Microdeploy(debug=True, port='COM4', baud=115200)
    """

    def __init__(self, config=None, debug=False, port=None, baud=None):
        self._debug = debug
        self._config_file = config
        self._config_override = {'device': {}}
        if port:
            self._config_override['device']['port'] = str(port)
        if baud:
            self._config_override['device']['baudrate'] = int(baud)
        self._setup()

    def _setup(self):
        self._config_object = config_module.Config(self._config_file, override=self._config_override)
        self._device_object = device_module.Device(self._config_object)
        self._package_object = package_module.Package(self._config_object)

        # Components definition  # FIXME: Find better names for articulating: deploy device ls - could be: project mcu ls (uproject, u

        class config(object):
            """Config information."""
            package = self._to_fire()(self._config_object.package)
            device = self._to_fire()(self._config_object.device)
            @self._to_fire()
            def show():
                """Return yaml configuration as pasred."""
                return self._config_object.config

        class device(object):
            """Access MCU filesystem and console."""
            console = self._to_fire()(self._device_object.console)
            get = self._to_fire()(self._device_object.get)
            ls = self._to_fire()(self._device_object.ls)
            mkdir = self._to_fire()(self._device_object.mkdir)
            rm = self._to_fire()(self._device_object.rm)
            rmdir = self._to_fire()(self._device_object.rmdir)
            run = self._to_fire()(self._device_object.run)
            reset = self._to_fire()(self._device_object.reset)
            @self._to_fire(doc_from=self._device_object.put)
            def put(filename, *args, **kwargs):
                def progress(state):
                    sys.stderr.write(state)
                    sys.stderr.flush()
                self._device_object.put(filename, *args, _progress=progress, **kwargs)

            class driver:
                """Under-the-hood, low-level drivers for communicating with MCU."""
                @self._to_fire()
                def ampy():
                    """Ampy driver for access to filesystem on MCU (`ampy.files.Files` object)"""
                    return self._device_object.ampy
                @self._to_fire()
                def pyboard():
                    """Ampy driver for repl access to MCU (`ampy.pyboard.Pyboard` object)"""
                    return self._device_object.pyboard
                # @self._to_fire()
                # def esptool():
                #     return self._device_object.esptool

        class package(object):
            """Upload package file to MCU."""
            names = self._to_fire()(self._package_object.names)
            files = self._to_fire()(self._package_object.files)
            @self._to_fire(doc_from=self._package_object.push)
            def push(*args, **kwargs):
                def progress(state):
                    sys.stderr.write(state)
                    sys.stderr.flush()
                return self._package_object.push(*args, _progress=progress, **kwargs)
            @self._to_fire()
            def show(name):
                """Show package definition (as of yaml config, with compiled `ignore` if applicable)."""
                return self._config_object.package(name)

        class cache(object):
            """Hashcache information."""
            def __init__(self_cache):
                self_cache.hashcache = self._device_object.hashcache
                # self_cache.hashcache = device_module._HashCache(self._device_object)
            @self._to_fire(decorate_with=None)
            def show(self):
                """Show contents of hashcache."""
                return self.hashcache._read(failsafe=False)
            @self._to_fire(decorate_with=None)
            def refresh(self):
                """Refresh hashcache from files contents on MCU."""
                return self.hashcache.refresh()
            @self._to_fire(decorate_with=None)
            def remove(self, filename):
                """Remove file from cache."""
                return self.hashcache.remove(filename)
            @self._to_fire(decorate_with=None)
            def clear(self):
                """Delete contents of hashcache."""
                return self.hashcache.clear()

        self.config = config
        self.device = device
        self.package = package
        self.cache = cache

    def ports(self):
        """List available serial ports on this system."""
        import serial.tools.list_ports
        ports = {}
        for port in serial.tools.list_ports.comports():
            ports[port.device] = port.description
        return ports

    # @property
    # def self(self):
    #     return {
    #         'debug': self._debug,
    #         'config_file': self._config_file,
    #         'config_override': self._config_override}

    # Decorators

    def _to_fire(self, doc_from=None, decorate_with=staticmethod):
        """
        Decorator for a function to fire CLI using signature and docstring from another function specified by `doc_from`.
        """
        def inner(f):
            def wrapper(*args, **kwargs):
                return self._handle_exception(f)(*args, **kwargs)
            f_doc = doc_from if doc_from else f
            signature = inspect_signature(f_doc)
            signature = signature.replace(parameters=[p for p in signature.parameters.values() if not p.name.startswith('_')])
            wrapper.__signature__ = signature
            wrapper.__doc__ = f_doc.__doc__
            wrapper.__annotations__ = f.__annotations__
            wrapper.__name__ = f.__name__
            if decorate_with is None:
                return wrapper
            else:
                return decorate_with(wrapper)
        return inner

    def _handle_exception(self, f):
        """
        Decorator for handling exceptions according `debug` (raise if debug else print exception).
        """
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (Exception, BaseException) as e:  # Note: PyboardError does not extend Exception
                # FIXME: This is duplicate with block except in `cli.MicrodeployCLI._setup`.
                if self._debug:
                    raise
                else:
                    sys.stderr.write(f'\nERROR: {e}\n\n')
                    sys.exit(1)  # also prevents `fire` from showing help screen
        return wrapper
