import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/wcag-audit-kit/scripts'))
from native_orca_runtime import NativeOrcaRuntime


class NativeOrcaStartupTest(unittest.IsolatedAsyncioTestCase):
    async def test_orca_is_not_launched_with_process_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home / 'packages'
            output = home / 'evidence'
            output.mkdir()
            for name in ('usr/bin/orca', 'usr/bin/Xvfb', 'usr/bin/speech-dispatcher',
                         'etc/speech-dispatcher/modules/espeak-ng.conf'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            (output / 'speechd.sock').touch()
            with (
                patch.dict(os.environ),
                patch('native_orca_runtime.NativeDisplay') as display,
                patch('native_orca_runtime.subprocess.run'),
                patch('native_orca_runtime.asyncio.sleep'),
            ):
                display.return_value.env = {}
                runtime = NativeOrcaRuntime(root, output)
                reader = Mock()
                reader.poll.return_value = 1
                try:
                    with patch.object(runtime, 'launch', side_effect=[Mock(), reader]) as launch:
                        with self.assertRaisesRegex(ValueError, r'orca\.stdout'):
                            await runtime.start()
                        command, name = launch.call_args.args
                        self.assertEqual(name, 'orca')
                        self.assertEqual(command[0], str(root / 'usr/bin/orca'))
                        self.assertNotIn('--replace', command)
                        self.assertNotIn('-r', command)
                finally:
                    await runtime.close()
