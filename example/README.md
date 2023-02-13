microdeploy-example
===================


Example project
---------------

Here is an example project, see files in [`examples/`](examples/).

```sh
cd example/project

cat microdeploy.yaml
microdeploy package names
```

Uploading a project on MCU:
```sh
microdeploy package files blink
microdeploy package push blink
microdeploy package push blink --port /dev/ttyUSB0
```

Uploading and running tests on MCU:
```sh
microdeploy package files tests
microdeploy package push tests
```