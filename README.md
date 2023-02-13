microdeploy
===========

**Deploy projects on MCU with a toolkit that is simple, fluid, and configurable.**


Features
--------

- Configurable per-project environments and files - see example config: [`microdeploy.yaml`](microdeploy.yaml)
- Workflow support with a consistent CLI and API - see [CLI Usage](#cli-usage) and [API Usage](#api-usage)
- Caching of MCU filesystem (hash cache)


Installation
------------

```sh
pip install microdeploy

microdeploy
microdeploy --help
```


CLI Usage
---------

```sh
microdeploy
microdeploy --help
microdeploy --config config-custom.yaml
microdeploy --port /dev/ttyUSB0 --baud 115200

microdeploy config
microdeploy config show

microdeploy device
microdeploy device show
microdeploy device ls
microdeploy device mkdir testdir
microdeploy device rmdir testdir
microdeploy device put main.py
microdeploy device put test.py main.py
microdeploy device rm main.py
microdeploy device rmdir .  # Note: Remove all files on MCU filesystem.

microdeploy device console

microdeploy package
microdeploy package show
microdeploy package show tests
microdeploy package files tests
microdeploy package put tests
microdeploy package put tests --debug --nofail --noput --norun --force
microdeploy package run tests-run.py

microdeploy package cache
microdeploy package cache show
microdeploy package cache refresh
microdeploy package cache clear
```


Python Usage
------------

```py
from microdeploy import Microdeploy
help(Microdeploy)

deploy = Microdeploy()
deploy.device.ls()
deploy.package.put('tests')

Microdeploy(config='deploy.yaml')
Microdeploy(config='deploy.yaml').device
Microdeploy(config='deploy.yaml').device.ls()
Microdeploy(debug=True, port='COM4', baud=115200)

```
See Python API in class [`Microdeploy`](pinout_deploy/__init__.py) in source code.


Example
-------

Automation of deploy and run tests:

```sh
microdeploy package push tests
```
```
Uploading to MCU: 8 files from package: tests...
Push: tests/test_pinout_pinwrap.py -> tests/test_pinout_pinwrap.py... 9747 bytes
      100%, 7.1s, 10939 bits/s, 0 bytes left, 0.0s left.
done.
Push: tests/test_pinout_pinout.py -> tests/test_pinout_pinout.py... 4059 bytes
      100%, 3.5s, 9361 bits/s, 0 bytes left, 0.0s left.
done.
Push: tests/__init__.py -> tests/__init__.py... 502 bytes
      100%, 1.2s, 3216 bits/s, 0 bytes left, 0.0s left.
done.
Push: tests/lib-micropython/unittest.py -> tests/lib-micropython/unittest.py... 7193 bytes
      100%, 5.5s, 10522 bits/s, 0 bytes left, 0.0s left.
done.
Push: tests-run.py -> main.py... 373 bytes
      100%, 1.2s, 2576 bits/s, 0 bytes left, 0.0s left.
done.
Push: pinout/__init__.py -> pinout/__init__.py... 6468 bytes
      100%, 5.0s, 10291 bits/s, 0 bytes left, 0.0s left.
done.
Push: pinout/watcher.py -> pinout/watcher.py... 2235 bytes
      100%, 2.3s, 7680 bits/s, 0 bytes left, 0.0s left.
done.
Push: pinout/pinwrap.py -> pinout/pinwrap.py... 6147 bytes
      100%, 4.8s, 10184 bits/s, 0 bytes left, 0.0s left.
done.

Run: tests-run.py...
Running on micropython (name='micropython', version=(1, 19, 1), _machine='ESP32 module with ESP32', _mpy=10246)
test_pinout_pinwrap_Pinwrap_value (TestPinoutPinwrap) ... ok
test_pinout_pinwrap_Pinwrap_config_without (TestPinoutPinwrap) ... ok
test_pinout_pinwrap_Pinwrap_config_with (TestPinoutPinwrap) ... ok
test_pinout_pinwrap_Pinwrap_subclass (TestPinoutPinwrap) ... ok
test_pinout_pinwrap_Pinwrap_subclasses (TestPinoutPinwrap) ... ok
test_helper_test_pinout_pinwrap_Pinwrap_subclass (TestPinoutPinwrap) ... ok
test_pinout_functions (TestPinoutPinout) ... ok
test_pinout_Pinout (TestPinoutPinout) ... ok
Ran 9 tests

OK.
```

More examples on asciinema:

- [Device access](https://asciinema.org/a/v0fogxAifNFMB7WoQG7nCVc6Q)

- [Cache management](https://asciinema.org/a/UTXTudQKR9ewKX0VzJLh7dVHz)

- [Configuration management](https://asciinema.org/a/q2KcZO7ilcrjLbYrB4NlPprFm)

- [Package management](https://asciinema.org/a/oPRYVrOjRq2mXGL6AFCIRKadr)


Development
-----------

Install and run from repository (without `setuptools`):
```sh
git clone ...
pip install -r requirements.txt

python -m microdeploy  # display cli help
python -m microdeploy --help
```

We follow [Semantic Versioning](https://semver.org/).