"""
Microdeploy CLI Executable.

Implement `DEFAULT_CONFIG_FILE` loading when no config file is specified with --config.

Usage:

    python -m deploy
"""

from . import Microdeploy
import fire
import sys

DEFAULT_CONFIG_FILE='microdeploy.yaml'

def run():
    fire.Fire(MicrodeployCLI, name='microdeploy')


class MicrodeployCLI(Microdeploy):
    """
    MCU deployment CLI.

    Arguments:
        --config  - use specific config file (default: {{default_config_file}})
        --port    - device port, overriding config
        --baud    - device baudrate, overriding config
        --debug   - print exception traceback, if any

    Usage:
        python -m microdeploy
        python -m microdeploy --help
        python -m microdeploy --config config-custom.yaml
        python -m microdeploy --port /dev/ttyUSB0 --baud 115200

        python -m microdeploy config
        python -m microdeploy config show
        python -m microdeploy device
        python -m microdeploy device show
        python -m microdeploy device console
        python -m microdeploy device ls
        python -m microdeploy device mkdir testdir
        python -m microdeploy device rmdir testdir
        python -m microdeploy device put main.py
        python -m microdeploy device put test.py main.py
        python -m microdeploy device rm main.py
        python -m microdeploy device rmdir .  # Note: Remove all files on MCU filesystem.
        python -m microdeploy package
        python -m microdeploy package show
        python -m microdeploy package show tests
        python -m microdeploy package files tests
        python -m microdeploy package put tests
        python -m microdeploy package put tests --debug --nofail --noput --norun --force
        python -m microdeploy package run tests-run.py
        python -m microdeploy package cache
        python -m microdeploy package cache show
        python -m microdeploy package cache refresh
        python -m microdeploy package cache clear
    """
    #   python -m microdeploy package pack example_ui  # TODO: make and upload a single python file including all imports starting from main.py
    #   python -m microdeploy flash erase
    #   python -m microdeploy flash write micropython.bin

    __doc__ = __doc__.replace('{{default_config}}', DEFAULT_CONFIG_FILE) 

    def __init__(self, config:str=DEFAULT_CONFIG_FILE, debug:bool=False, port:str=None, baud:int=None):
        super().__init__(config=config, debug=debug, port=port, baud=baud)

    def _setup(self):
        try:
            super()._setup()
            if not self._config_object.device()['port']:
                sys.stderr.write(f"Note: Device port not specified: use --port {f'or edit config file: {self._config_file}' if self._config_file else ''}\n")
            if not self._device_object.hashcache._cachefile_is_readwrite():
                sys.stderr.write(f'Note: Cache file is not read/write: {self._device_object.hashcache.cachefile}\n')

        except FileNotFoundError as e:
            if self._config_file != DEFAULT_CONFIG_FILE:
                raise
            if not self._config_override['device'].get('port'):
                sys.stderr.write(f'Note: Default config file not found: {self._config_file} (you can create this default file, or use --config another.yaml)\n')
            self._config_file = None
            self._setup()  # let the user continue without a default config file

        except KeyboardInterrupt as e:
            sys.stderr.write('\nAborted by user.\n')

        except (Exception, BaseException) as e:  # Note: PyboardError does not extend Exception
            if self._debug:
                raise
            else:
                sys.stderr.write(f'\nERROR: {e}\n\n')
                sys.exit(1)  # also prevents `fire` from showing help screen
