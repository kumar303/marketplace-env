import os
from unittest import TestCase

import mock

import cmds


class TestCommands(TestCase):

    def setUp(self):
        self.parser = cmds.create_parser()

    @mock.patch('cmds.BRANCHES', ['foo'])
    @mock.patch('cmds.TREES_DIR', '/dir/')
    def test_checkout_command(self):
        """Test checkout cmd sees correct args."""

        args = self.parser.parse_args(['checkout'])
        with mock.patch("cmds.subprocess") as subprocess:

            cmds.checkout(args, self.parser, 'gh-user')

            self.assertEqual(subprocess.call.call_args_list, [
                mock.call([
                    'git', 'clone', '-o', 'upstream',
                    'git@github.com:mozilla/foo.git',
                    '/dir/foo'
                ]),
                mock.call([
                    'git', 'remote', 'add', 'origin',
                    'git@github.com:gh-user/foo.git'
                ], cwd='/dir/foo'),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'origin'
                ])
            ])

    @mock.patch('cmds.BRANCHES', ['foo'])
    @mock.patch('cmds.TREES_DIR', '/dir/')
    def test_checkout_command_inverted_origin_upstream(self):
        """Test checkout cmd sees correct args when origin is inverted."""

        args = self.parser.parse_args([
            'checkout',
            '--moz_remote_name', 'origin',
            '--fork_remote_name', 'upstream'
        ])
        with mock.patch("cmds.subprocess") as subprocess:

            cmds.checkout(args, self.parser, 'gh-user')

            self.assertEqual(subprocess.call.call_args_list, [
                mock.call([
                    'git', 'clone', '-o', 'origin',
                    'git@github.com:mozilla/foo.git',
                    '/dir/foo'
                ]),
                mock.call([
                    'git', 'remote', 'add', 'upstream',
                    'git@github.com:gh-user/foo.git'
                ], cwd='/dir/foo'),
                mock.call([
                    'git', 'config',
                    'branch.master.remote', 'upstream'
                ])
            ])

    def test_bind_ip(self):
        args = self.parser.parse_args(['bind', '--bind_ip', '10.0.0.2'])

        p = mock.patch('cmds.get_adb_devices')
        p.start().return_value = ['abcde      device']
        self.addCleanup(p.stop)

        def mock_shell(args, **kw):
            if args[0:2] == ['adb', 'pull']:
                if os.path.exists('./hosts'):
                    raise RuntimeError(
                        'Expected to be running in a temp dir!')
                with open('./hosts', 'w') as f:
                    f.write('mock hosts file')

        with mock.patch('cmds.subprocess') as subprocess:
            subprocess.check_call.side_effect = mock_shell

            cmds.bind(args, self.parser)

            self.assertEqual(subprocess.check_call.call_args_list, [
                mock.call(['adb', 'remount']),
                mock.call(['adb', 'pull', '/system/etc/hosts', './']),
                mock.call(['adb', 'push', './new-hosts', '/system/etc/hosts'])
            ])
