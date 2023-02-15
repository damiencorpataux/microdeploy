import microdeploy
import unittest

class Test(unittest.TestCase):

    def test_microdeploy_config_make_filename_relative(self):

        config = microdeploy.config.Config('tests/samples/microdeploy_empty.yaml')
        self.assertEqual(config.make_filename_relative('some-file'), 'tests/samples/some-file')
        self.assertEqual(config.make_filename_relative(''), 'tests/samples')

        config = microdeploy.config.Config()
        self.assertEqual(config.make_filename_relative('hello.txt'), 'hello.txt')
        self.assertEqual(config.make_filename_relative('say/hello.txt'), 'say/hello.txt')
        self.assertEqual(config.make_filename_relative('./hello.txt'), 'hello.txt')
        self.assertEqual(config.make_filename_relative('../hello.txt'), '../hello.txt')


    def test_microdeploy_config_make_filenames(self):

        config = microdeploy.config.Config()
        with self.assertRaisesRegex(TypeError, 'missing \d+ required positional argument', msg='Function signature'):
            config.make_filenames()
        with self.assertRaisesRegex(ValueError, 'File definition must be string or list'):
            config.make_filenames(123)
        with self.assertRaisesRegex(ValueError, 'File definition must be string or list'):
            config.make_filenames({})
        with self.assertRaisesRegex(ValueError, 'File definition must be string or list'):
            config.make_filenames(['filename.ext'])

        config = microdeploy.config.Config()
        with self.assertRaisesRegex(AssertionError, 'Packages not available when no config file'):
            config.package('any')  # make_filenames() doesn't need to work when no config.

        # FIXME: make a definition of tests for make_filenames(), reuse it for documentation ?
        # eg. [[given_argument, result_expected]
        # eg = [
        #     ['source.ext', [('tests/samples/source.ext', 'source.ext')]]
        # ]
        config = microdeploy.config.Config('tests/samples/microdeploy_empty.yaml')
        self.assertEqual(config.make_filenames('source.ext'), [
            ('tests/samples/source.ext', 'source.ext')])

        self.assertEqual(config.make_filenames('files/source.ext'), [
            ('tests/samples/files/source.ext', 'files/source.ext')])

        self.assertEqual(config.make_filenames(['source.ext', 'destination.ext']), [
            ('tests/samples/source.ext', 'destination.ext')])

        self.assertEqual(config.make_filenames(['files/source.ext', 'destination.ext']), [
            ('tests/samples/files/source.ext', 'destination.ext')])

        self.assertEqual(config.make_filenames(['source.ext', 'files/destination.ext']), [
            ('tests/samples/source.ext', 'files/destination.ext')])

        self.assertEqual(config.make_filenames('files/*'), [
            ('tests/samples/files/main.py', 'files/main.py'),  # FIXME: wrong! destination must be: files/main.py
            ('tests/samples/files/README.md', 'files/README.md'),
            ('tests/samples/files/component.py', 'files/component.py')])

        self.assertEqual(config.make_filenames('files/*/*'), [
            ('tests/samples/files/lib/module.py', 'files/lib/module.py')])

        self.assertEqual(config.make_filenames('files/*.py'), [
            ('tests/samples/files/main.py', 'files/main.py'),
            ('tests/samples/files/component.py', 'files/component.py')])

        self.assertEqual(config.make_filenames('files/*/*.py'), [
            ('tests/samples/files/lib/module.py', 'files/lib/module.py')])

        self.assertEqual(config.make_filenames('files/*.non-existing'), [
            ])

        self.assertEqual(config.make_filenames('files/**'), [
            ('tests/samples/files/main.py', 'files/main.py'),
            ('tests/samples/files/README.md', 'files/README.md'),
            ('tests/samples/files/component.py', 'files/component.py'),
            ('tests/samples/files/lib/sublib/submodule.py', 'files/lib/sublib/submodule.py'),
            ('tests/samples/files/lib/module.py', 'files/lib/module.py')])

        self.assertEqual(config.make_filenames('files/**/*.py'), [
            ('tests/samples/files/main.py', 'files/main.py'),
            ('tests/samples/files/component.py', 'files/component.py'),
            ('tests/samples/files/lib/module.py', 'files/lib/module.py'),
            ('tests/samples/files/lib/sublib/submodule.py', 'files/lib/sublib/submodule.py')])

        # print(config.make_filenames('files/*'))  # TODO: destination directory specification
        # print(config.make_filenames(['files/*', '.']))  # TODO
        # print(config.make_filenames(['files/*', 'another_dir']))  # TODO
        # print(config.make_filenames(['files/*', 'another_dir/']))  # TODO
        # print(config.make_filenames(['files/*', 'another_dir/subdir']))  # TODO
        # print(config.make_filenames(['files/*', 'another_dir/subdir/']))  # TODO

        # print(config.make_filenames('files/')  # FIXME?

    def test_example_project_microdot(self):
        # # TODO?
        # mdeploy = microdeploy.Microdeploy(config='..example/project-microdot/microdeploy.yaml')
        # mdeploy.package.push('tests')
        pass
