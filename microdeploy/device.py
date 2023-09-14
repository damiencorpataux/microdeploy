"""
Microdeploy Device (mcu) manager.
"""
# Note: source files related to ampy:
#   https://github.com/scientifichackers/ampy/blob/master/ampy/pyboard.py
#   https://github.com/scientifichackers/ampy/blob/master/ampy/files.py

from .config import Configurable
from ampy import pyboard as ampy_pyboard
from ampy import files as ampy_files
import terminal_s.terminal
import time
import sys
import os

# FIXME:
#   let handle wildcards (glob style) * for put(), rm(), rmdir()  - Note: rm seem to be able to delete directories too
#   let handle --recursive for put()                              - Note: rm() and rmdir() seem to be recusrive only

class Device(Configurable):

    __doc__ = __module__.__doc__

    @property
    def pyboard(self):
        """Return singleton instance of `ampy.pyboard.Pyboard`."""
        if not self._pyboard:
            self._pyboard = ampy_pyboard.Pyboard(self.config.device()['port'], baudrate=self.config.device()['baudrate'], user='micro', password='python', wait=0, rawdelay=0)
        return self._pyboard

    @property
    def ampy(self):
        """Return singleton instance of `ampy.files.Files`."""
        if not self._ampy:
            self._ampy = ampy_files.Files(self.pyboard)
        return self._ampy

    def __init__(self, config):
        super().__init__(config)
        self._pyboard = None
        self._ampy = None
        self.hashcache = _HashCache(self)

    def console(self, **overrides):
        """Open serial console to MCU."""
        device_config = self.config.device(**overrides)
        terminal_s.terminal.run(
            port=device_config['port'],
            baudrate=device_config['baudrate'])

    def ls(self, directory='/', recursive=True, long=False):
        """Return files on MCU filesystem."""
        return self.ampy.ls(directory, recursive=recursive, long_format=long)

    def get(self, filename):
        """Return file content from MCU filesystem."""
        return self.ampy.get(filename)

    def put(self, source, destination=None, force=False, parents_create=True, _progress=lambda state: None):
        """Upload file to MCU filesystem, creating parent directories."""
        if destination is None:
            destination = source
        with open(source, 'rb') as f:
            data = f.read()
        progress = _Progress(source, callback_for_user=_progress)
        if not force and self.hashcache.same(destination, data):
            _progress(f'Ign: {source}\n  -> {destination} ... up-to-date in cache, --force to override.\n')
        else:
            _progress(f'Put: {source}\n  -> {destination} ... {progress.bytes} bytes\n')
            try:
                progress.start()
                self.ampy.put(destination, data, progress_cb=progress.callback_for_ampy)  # FIXME: ampy version from pip is too old to include feature progress.
                self.hashcache.add(destination, data)
            except ampy_pyboard.PyboardError as e:
                if not parents_create:
                    raise RuntimeError(f'Directory does not exist for file: {destination}')
                elif len(e.args) > 1 and 'ENOENT' in str(e.args[2]):
                    self.mkdir(os.path.dirname(destination), parents_create=True)
                    _progress(f'\n\nCreating directory: {os.path.dirname(destination)}\n\n')
                    return self.put(source, destination, force, parents_create, _progress)
                else:
                    raise

    def rm(self, filename):
        """Remove file from MCU filesystem."""
        self.ampy.rm(filename)
        self.hashcache.remove(filename)

    def mkdir(self, directory, parents_create=True):
        """Create directory on MCU filesystem (creating parents)."""
        try:
            return self.ampy.mkdir(directory)
        except ampy_pyboard.PyboardError as e:
            if 'OSError: [Errno 2] ENOENT' in str(e):
                if not parents_create:
                    raise RuntimeError(f'Parent directory does not exist for: {directory}')
                else:
                    path_parts = filter(bool, directory.split(os.path.sep))
                    path = ''
                    for path_part in path_parts:
                        path += f'/{path_part}'
                        try:
                            self.ls(path)
                        except RuntimeError as e:
                            if 'No such directory' in str(e):
                                self.mkdir(path, parents_create=True)
                            else:
                                raise

    def rmdir(self, filename):
        """Remove directory from MCU filesystem."""
        try:
            self.ampy.rmdir(filename)
        except RuntimeError as e:
            if filename in ['', '.'] and 'No such directory' in str(e):  # ampy rmdir . remove all files from filesystem and raise exception
                sys.stderr.write('Deleting all files...\n')
                self.hashcache.clear()
            else:
                raise


    def run(self, filename):
        """Run python script on MCU (without storing on filesystem)."""
        try:
            return self.ampy.run(filename)
        except ampy_pyboard.PyboardError as e:
            raise ampy_pyboard.PyboardError(str(e.args[2].decode('utf-8')))

    def reset(self):
        """Reset MCU (hard reset)."""
        self.pyboard.enter_raw_repl()
        self.pyboard.exec_raw_no_follow("""if 1:  # hack indent error
            try:
                import microcontroller as m
            except:
                import machine as m
            m.reset()
        """)
        self.pyboard.exit_raw_repl()


# Helpers

import hashlib
import json

class _HashCache(object):
    """
    Pseudo-cache for files on MCU (using hashes).
    """ 
    # FIXME: when config will multiple devices, the hashcache must handle multiple caches,
    #   ie. one additional level in hashcash json structure;
    #   also, instanciable class could be nice.

    def __init__(self, device:Device, cachefile='.microdeploy.hashcache'):
        self.device = device
        self.cachefile = cachefile

    def same(self, mcu_filename, content_to_compare):
        """Return `True` if hash in cache for mcu_filename matches hash of `content_to_compare`."""
        return self.get(mcu_filename) == self._hash(content_to_compare)

    def get(self, mcu_filename):
        """Return hash from cache for `mcu_filename`, or return None."""
        mcu_filename = self._mcu_filename(mcu_filename)
        return self._read().get(mcu_filename)

    def add(self, mcu_filename, file_contents):
        """Add hash to cache for `mcu_filename` and `file_contents`."""
        hashcache = self._read()
        mcu_filename = self._mcu_filename(mcu_filename)
        hashcache[mcu_filename] = self._hash(file_contents)
        self._write(hashcache)

    def remove(self, mcu_filename):
        """Remove hash from cache for `mcu_filename`."""
        hashcache = self._read()
        mcu_filename = self._mcu_filename(mcu_filename)
        if mcu_filename in hashcache:
            del hashcache[mcu_filename]
            self._write(hashcache)

    def clear(self):
        """Remove cache file."""
        self._write({})
        sys.stderr.write(f'Cache file cleared: {self.cachefile}.\n')
        # try:
        #     os.unlink(self.cachefile)
        #     sys.stderr.write(f'Cache file deleted: {self.cachefile}.\n')
        # except FileNotFoundError:
        #     sys.stderr.write(f'Cache already clear: {self.cachefile}\n')

    def refresh(self):
        """Refresh cache from files contents on MCU."""
        hashcache = {}
        files_on_device = self.device.ls('/')
        for filename in files_on_device:
            sys.stderr.write(f"{' '*50} (downloading) {filename}")
            sys.stderr.flush()
            last_hashcache = self._read()
            try:
                file_content = self.device.get(filename)
                hashcache[filename] = self._hash(file_content)
                sys.stderr.write(f"\r{hashcache[filename]} {filename}  ")
                if hashcache[filename] == last_hashcache.get(filename):
                    sys.stderr.write('(not modified)')
                else:
                    sys.stderr.write('(modified)' if last_hashcache.get(filename) else '(new)')
                    self._write(dict(last_hashcache, **hashcache))  # actual cache write
            except RuntimeError as e:
                if 'No such file' not in str(e): raise   # pass when file is a directory
                sys.stderr.write(f"\r{' '*52} (directory) {filename}  (not caching)")
            # except Exception as e:
            #     sys.stderr.write(f'(error) {filename}: {e}')
            sys.stderr.write(f"\n")
        for filename in set(last_hashcache) - set(files_on_device):
            hash = last_hashcache[filename]
            del last_hashcache[filename]
            self._write(last_hashcache)
            sys.stderr.write(f'{hash} {filename}  (deleted)\n')  # for information

    def _write(self, hashcache):
        """Write `hashcache` to file `_HashCache.cachefile`, replacing existing content."""
        try:
            with open(self.cachefile, 'w') as f:
                f.write(json.dumps(hashcache))
        except PermissionError as e:
            sys.stderr.write(f'Bypassing cache write: file not writable: {self.cachefile}\n')

    def _read(self, failsafe=True):
        """Return hashcache content from file `_HashCache.cachefile`"""
        try:
            try:
                with open(self.cachefile) as f:
                    cache = json.loads(f.read())  # actual loading of file
                    if type(cache) is dict:
                        return cache
                    else:
                        raise ValueError(f'Bypassing cache: invlid cache structure in: {self.cachefile}')
            except FileNotFoundError as e:
                sys.stderr.write(f'Creating file: {self.cachefile}\n')
                return {}
            except json.decoder.JSONDecodeError as e:
                sys.stderr.write(f'Clearing hashcache: invalid json in: {self.cachefile})\n')
                return {}
            except PermissionError as e:
                raise PermissionError(f'Bypassing cache read: file not readable: {self.cachefile}')
        except Exception as e:
            if failsafe:
                sys.stderr.write(f'{e}\n')
                return {}
            else:
                raise e.__class__(f'Cache error: {e}')

    def _hash(self, bytes):
        return hashlib.sha256(bytes).hexdigest()

    def _mcu_filename(self, mcu_filename):
        return os.path.join('/', mcu_filename)  # file format like `ls()` always starting with /

    def _cachefile_is_readwrite(self):
            return (
                (os.path.exists(self.cachefile) and os.path.isfile(self.cachefile) and os.access(self.cachefile, os.R_OK) and os.access(self.cachefile, os.W_OK))  # file exists and is read/writable
                or (not os.path.exists(self.cachefile) and os.access('.', os.W_OK)))  # file not exists and containing directory is writable


class _Progress(object):
    """
    Link callback of `ampy.files.Files.put(progress_cb)` to `callback of device.put(_progess)`.
    """
    def __init__(self, filename, callback_for_user=None):
        self.bytes = os.stat(filename).st_size
        self.bytes_left = self.bytes
        self.callback = callback_for_user or (lambda state: None)

    def start(self):
        self.time_start = time.time_ns()
        self.callback(self._message_during())
        if self.bytes == 0:
            self.callback('\n')

    def callback_for_ampy(self, bytes_uploaded):
        self.callback('\b' * len(self._message_during()))
        self.bytes_left -= bytes_uploaded
        self.callback(self._message_during())
        if self.bytes_left == 0:
            self.callback('\n')
        # if self.bytes_left == 0:
        #     self.callback('\b' * len(self._message_during()))
        #     self.callback(self._message_after())

    def _message_during(self):
        time_elapsed = (time.time_ns() - self.time_start) / 10**9
        bitrate = (self.bytes - self.bytes_left) / time_elapsed * 8
        time_left = 0 if not bitrate else self.bytes_left*8 / (bitrate)
        percent = 100 if not self.bytes else (self.bytes - self.bytes_left) / self.bytes * 100
        return f'\r     {percent:>3.0f}%, {time_elapsed:.1f}s, {bitrate:.0f} bits/s, {str(self.bytes_left)} bytes left, {time_left:.1f}s left. '

    # def _message_after(self):
    #     percent = (self.bytes - self.bytes_left) / self.bytes * 100
    #     return f'\r{percent:.0f}%, {str(self.bytes)} bytes uploaded.'
