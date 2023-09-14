from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='microdeploy',
    version='0.0.2',
    description='Micropython deployment toolchain',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/damiencorpataux/microdeploy',
    keywords='micropython, deploy, deployment, microcontroller, mcu, serial, ampy, rshell, picocom, console, cache, caching',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Shells',
        'Topic :: Terminals :: Serial',
        'Topic :: Utilities',
    ],
    author='Damien Corpataux',
    author_email='d@mien.ch',
    license='MIT',
    packages=['microdeploy'],
    zip_safe=False,
    install_requires=[
        'adafruit-ampy-master',
        'terminal-s',
        'pyserial',
        'PyYAML',
        'fire'
    ],
    entry_points = {'console_scripts': ['microdeploy=microdeploy.cli:run']})
