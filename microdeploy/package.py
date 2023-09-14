"""
Microdeploy Package manager.
"""

from . import device
from .config import Configurable
import re
import os
import time  # FIXME


class Package(Configurable):

    def __init__(self, config):
        super().__init__(config)
        self.device = device.Device(self.config)

    def names(self):
        """Return packages names."""
        return list(self.config.config['packages'].keys())

    def files(self, name):
        """Return packages files."""
        return self.config.package_files(name)

    def push(self, name, force=False, noput=False, norun=False, nofail=False, _progress=lambda state: None):
        """Upload package files to MCU."""
        files = self.config.package_files(name)
        count = 0
        _progress(f'Deploying package: {name}: {len(files)} files -> MCU...\n\n')
        if not noput:
            for source, destination in files:
                try:
                    mpycross_version = None  # FIXME: Move this outside loop `for`.
                    mpycross_args = self.config.config['packages'][name].get('mpy', False)
                    if mpycross_args and source.endswith('.py') and destination != 'main.py':
                        if not mpycross_version:
                            try:
                                import mpy_cross
                                import subprocess
                                mpycross_version = mpy_cross.run('--version', stdout=subprocess.PIPE).communicate()[0].decode().strip()
                            except Exception as e:
                                raise e.__class__(f'Please install mpy-cross: `pip install mpy-cross` - {e}')
                        mpycross_args = mpycross_args if type(mpycross_args) in [list, tuple] else []#'-march=xtensawin']#, '-X', 'emit=native']
                        mpy_cross.run(source, *mpycross_args)
                        source = re.sub('\.py$', '.mpy', source)
                        destination = re.sub('\.py$', '.mpy', destination)
                        time.sleep(.1)  # FIXME: Fixes sometimes .mpy file is not found (but exists on disk)
                        print(f'Compiled {source} to destination {destination} - using `mpy-cross {" ".join(mpycross_args)}` (with version: {mpycross_version})')
                        self.device.put(source, destination, parents_create=True, force=force, _progress=_progress)
                        os.remove(source)  # .mpy file
                    else:
                        self.device.put(source, destination, parents_create=True, force=force, _progress=_progress)
                    count += 1
                    _progress('\n')
                except Exception as e:
                    if nofail:
                        _progress(f'ERROR: {e.__class__.__name__}: {e}\n')
                    else:
                        raise
        else:
            _progress(f'Put: Skipping.\n\n')

        files_to_run = self.config.config['packages'][name].get('run', [])
        for file_to_run in files_to_run:
            _progress(f'Run: {file_to_run}... ')
            if norun:
                _progress('skipping.\n')
            else:
                _progress('\n')
                file_to_run = self.config.make_relative_to_configfile(file_to_run)
                _progress('---8<---------\n')
                self.device.run(file_to_run)
                _progress('--------->8---\n')

        if self.config.config['packages'][name].get('reset', False):
            _progress(f'Reset MCU... ')
            self.device.reset()
            _progress(f'done.\n')

        _progress('\n')
        if count == len(files) or noput:
            _progress(f"OK: Pushed to MCU {count}/{len(files)} files from package: {name}{' (skipped by --noput)' if noput else ''}.\n")
        if not noput and count != len(files):
            _progress(f'WARNING: Only {count}/{len(files)} files uploaded from package: {name} !\n')
        if files_to_run:
            _progress(f"Ran on MCU: {files_to_run}{ '(skipped by --norun)' if norun else ''}.\n")

    # def stats(self, name):
    #     # TODO: for file in package: display count lines/bytes/words/spaces/emptylines + total for package
    #     pass

    # def pack(self, name):
    #     # TODO: create a single file with all files of a package (respecting imports)
    #     pass

    # def run(self, name):
    #     # TODO: ampy run <a packed package> (may be too slow to upload for a single run ?)
    #     pass
