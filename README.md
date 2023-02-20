microdeploy
===========

**Deploy project files on MCU as simple, fluid, and configurable.**

This tool gives a per-project approach for uploading files to MCU.
Per-environment support is intended - todo.


Features
--------

- Configurable project files and environment - see example config: [`microdeploy.yaml`](example/project/microdeploy.yaml)
- Workflow support with a consistent CLI and API - see [CLI Usage](#cli-usage) and [Python Usage](#python-usage)
- Pseudo-caching of MCU filesystem (hash cache)


Purpose
-------

A KISS approach to wrap up existing CLI tools:
[ampy](https://pypi.org/project/adafruit-ampy-master/),
[terminal-s](https://pypi.org/project/terminal-s/),
(esptool, rshell),
and [fire](https://pypi.org/project/fire/).

&mdash; *Note: Package [`adafruit-ampy-master`](https://pypi.org/project/adafruit-ampy-master/) is used
instead of [adafruit-ampy](https://pypi.org/project/adafruit-ampy/)
in order to allow upload progress display, because the official package is not up-to-date with [master](https://github.com/damiencorpataux/ampy).*


Installation
------------

```s
pip uninstall adafruit-ampy  # see requirements.txt (this is 0.0.1)
pip install --user microdeploy
```
```s
microdeploy
microdeploy --help
```


CLI Usage
---------

```s
microdeploy                          # With default config file: microdeploy.yaml
microdeploy --port /dev/ttyUSB0      # Without config file
microdeploy --config other.yaml      # Use alternate config file
microdeploy --baud 115200 --port XYZ  # Override config

microdeploy config
microdeploy config show

microdeploy device
microdeploy device show
microdeploy device ls
microdeploy device put main.py
microdeploy device put test.py main.py
microdeploy device rm main.py
microdeploy device mkdir testdir
microdeploy device rmdir testdir
microdeploy device rmdir .  # Note: Remove all files on MCU filesystem.

microdeploy device console

microdeploy package
microdeploy package names
microdeploy package files tests
microdeploy package push tests
microdeploy package push tests --debug --nofail --noput --norun --force
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
```

Without config file:
```py
deploy = Microdeploy(port='/dev/ttyUSB0')

deploy.config.show()
deploy.device.ls()
deploy.device.put('main.py')
deploy.device.put('lib.py', '/lib/lib.py')

deploy.device.run('sandbox/test-something.py')
deploy.device.reset()
```

With config file (relative to cwd):
```py
deploy = Microdeploy(config='microdeploy.yaml')

deploy.package.show('tests')
deploy.package.files('tests')
deploy.package.push('tests')
```


Example
-------
Automation of deploy and run tests on MCU - see code in [`example/project`](example/project).

Push the package (2 times to see the cache working):
```s
python3 -m microdeploy -c example/project/microdeploy.yaml package push tests-run
```
```s
Deploying package: tests-run: 4 files -> MCU...

Put: example/project/tests/__init__.py
  -> tests/__init__.py... 23 bytes
       0%, 0.0s, 0 bits/s, 23 bytes left, 0.0s left.

Creating directory: tests

Put: example/project/tests/__init__.py
  -> tests/__init__.py... 23 bytes
     100%, 0.9s, 209 bits/s, 0 bytes left, 0.0s left.

Put: example/project/tests/test_pin.py
  -> tests/test_pin.py... 579 bytes
     100%, 1.3s, 3596 bits/s, 0 bytes left, 0.0s left.

Put: example/project/tests/lib/unittest.py
  -> tests/lib/unittest.py... 7193 bytes
       0%, 0.0s, 0 bits/s, 7193 bytes left, 0.0s left.

Creating directory: tests/lib

Put: example/project/tests/lib/unittest.py
  -> tests/lib/unittest.py... 7193 bytes
     100%, 5.4s, 10559 bits/s, 0 bytes left, 0.0s left.

Put: example/project/tests-run.py
  -> tests-run.py... 55 bytes
     100%, 0.9s, 490 bits/s, 0 bytes left, 0.0s left.

Run: tests-run.py...
---8<---------
test_pin_on (TestPin) ... ok
test_pin_off (TestPin) ... ok
test_pin_toggle (TestPin) ... ok
Ran 3 tests

OK
--------->8---

OK: Pushed to MCU 4/4 files from package: tests-run.
Ran on MCU: ['tests-run.py'].
```

More on asciinema:

- [Device access](https://asciinema.org/a/v0fogxAifNFMB7WoQG7nCVc6Q)

- [Cache management](https://asciinema.org/a/UTXTudQKR9ewKX0VzJLh7dVHz)

- [Configuration management](https://asciinema.org/a/q2KcZO7ilcrjLbYrB4NlPprFm)

- [Package management](https://asciinema.org/a/oPRYVrOjRq2mXGL6AFCIRKadr)


Development
-----------

This prototype was written because I was tinkering with ESP in a project with multiple files.
I was tired of forgetting to upload this or that file, and testing partly outdated code,
<br>or needing to upload all files again every time. It became worse when I had to test my project on both ESP32 and 8266.

Project facts:

* [Semantic Versioning](https://semver.org/) is followed

* Stage of development: [MVP](https://en.wikipedia.org/wiki/Minimum_viable_product)

* The smaller the better:
   ```wc -l microdeploy/*```
   ```s
    91 microdeploy/cli.py
   103 microdeploy/config.py
   293 microdeploy/device.py
   197 microdeploy/__init__.py
     6 microdeploy/__main__.py
    77 microdeploy/package.py
   767 total
   ```
