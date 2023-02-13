"""
Microdeploy Device (mcu) manager.
"""
# Note: source files related to ampy:
#   https://github.com/scientifichackers/ampy/blob/master/ampy/pyboard.py
#   https://github.com/scientifichackers/ampy/blob/master/ampy/files.py

from .config import Configurable
# import ampy.pyboard
# import ampy.files
from .ampy import pyboard as ampy_pyboard
from .ampy import files as ampy_files
import terminal_s.terminal
import time
import sys
import os

# FIXME:
#   let handle wildcards (glob style) * for put(), rm(), rmdir()  - Note: rm seem to be able to delete directories too
#   let handle --recursive for put()                           - Note: rm() and rmdir() seem to be recusrive only

class Device(Configurable):

    # ampy = None
    # pyboard = None
    __doc__ = __module__.__doc__

    def __init__(self, config):
        super().__init__(config)
        device_config = self.config.device()
        self.pyboard = ampy_pyboard.Pyboard(device_config['port'], baudrate=device_config['baudrate'], user='micro', password='python', wait=0, rawdelay=0)
        self.ampy = ampy_files.Files(self.pyboard)
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

    def put(self, source, destination=None, force=False, parents_create=True, _progress=None):
        """Upload file to MCU filesystem."""
        if destination is None:
            destination = source
        with open(source, 'rb') as f:
            data = f.read()
        progress = _Progress(source, callback_for_user=_progress)
        if not force and self.hashcache.same(destination, data):
            _progress(f'Ign: {source}\n  -> {destination}... up-to-date in cache, --force to override.\n')
        else:
            _progress(f'Put: {source}\n  -> {destination}... {progress.bytes} bytes\n')
            try:
                progress.start()
                self.ampy.put(destination, data, progress_cb=progress.callback_for_ampy)  # FIXME: ampy version from pip is too old to include feature progress.
                self.hashcache.add(destination, data)
            except ampy.pyboard.PyboardError as e:
                if not parents_create:
                    raise RuntimeError(f'Directory does not exist for file: {destination}')
                else:
                    self.mkdir(os.path.dirname(destination), parents_create=True)
                    return self.ampy.put(source, destination)

    def rm(self, filename):
        """Remove file from MCU filesystem."""
        self.ampy.rm(filename)
        self.hashcache.remove(filename)

    def mkdir(self, directory, parents_create=True):
        """Create directory on MCU filesystem (creating parents)."""
        try:
            return self.ampy.mkdir(directory)
        except ampy.pyboard.PyboardError as e:
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
        self.ampy.rmdir(filename)
        if filename in ['', '.']:
            self.hashcache.delete()

    def run(self, filename):
        """Run python script on MCU (without storing on filesystem)."""
        return self.ampy.run(filename)


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

    def __init__(self, device:Device, cachefile='.deploy.hashcache'):
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
        try:
            os.unlink(self.cachefile)
            sys.stderr.write(f'Hashcache file deleted: {self.cachefile}.\n')
        except FileNotFoundError:
            sys.stderr.write(f'Hashcache already clear: {self.cachefile}\n')

    def refresh(self):
        """Refresh cache from files contents on MCU."""
        last_hashcache = self._read()
        hashcache = {}
        files_on_device = self.device.ls('/')
        for filename in files_on_device:
            try:
                file_content = self.device.get(filename)
                hashcache[filename] = self._hash(file_content)
                print(f"{hashcache[filename]} {filename} {'(unchanged)' if hashcache[filename] == last_hashcache.get(filename) else  '(changed)' if last_hashcache.get(filename) else '(new)'}")
            except RuntimeError as e:
                if 'No such file' not in str(e): raise   # pass when file is a directory
                print(f"{' '*51}(not caching) {filename} (directory)")
            except Exception as e:
                sys.stderr.write(f'Error with file: {filename}: {e}\n')
        self._write(hashcache)
        for filename in set(last_hashcache) - set(files_on_device):
            print(f'{last_hashcache[filename]} {filename} (removed)')  # for information

    def _write(self, hashcache):
        """Write `hashcache` to file `_HashCache.cachefile`, replacing existing content."""
        with open(self.cachefile, 'w+') as f:
            f.write(json.dumps(hashcache))

    def _read(self):
        """Return hashcache content from file `_HashCache.cachefile`"""
        try:
            if os.path.isfile(self.cachefile) and os.access(self.cachefile, os.W_OK):
                with open(self.cachefile) as f:
                    return json.loads(f.read())  # actual loading of hashcache file
            else:
                sys.stderr.write(f'Bypassing cache: hashcache file not writable: {self.cachefile}\n')
                return {}

        except FileNotFoundError as e:
            sys.stderr.write(f'Creating hashcache file: {self.cachefile}\n')
            return {}
        except json.decoder.JSONDecodeError as e:
            sys.stderr.write(f'Resetting hashcache file: invalid json content in: {self.cachefile})\n')
            return {}

    def _hash(self, bytes):
        return hashlib.sha256(bytes).hexdigest()

    def _mcu_filename(self, mcu_filename):
        return os.path.join('/', mcu_filename)  # file format like `ls()` always starting with /


class _Progress(object):
    """
    Link callback of `ampy.files.Files.put(progress_cb)` to `callback of device.put(_progess)`.
    """
    def __init__(self, filename, callback_for_user=None):
        self.bytes = os.stat(filename).st_size
        self.bytes_left = self.bytes
        self.callback = callback_for_user

    def start(self):
        self.time_start = time.time_ns()
        self.callback(self._message_during())

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
        percent = (self.bytes - self.bytes_left) / self.bytes * 100
        return f'\r     {percent:>3.0f}%, {time_elapsed:.1f}s, {bitrate:.0f} bits/s, {str(self.bytes_left)} bytes left, {time_left:.1f}s left. '

    # def _message_after(self):
    #     percent = (self.bytes - self.bytes_left) / self.bytes * 100
    #     return f'\r{percent:.0f}%, {str(self.bytes)} bytes uploaded.'