import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'nao/bridge'/file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
manager=load('manager25','manage.py')
runner=load('runner25','runner.py')

class NaoTests(unittest.TestCase):
    def fake_qi(self,version,revision='VERSION_40'):
        qi=Mock();qi.Session.return_value.service.return_value.systemVersion.return_value.value.return_value=version
        qi.Session.return_value.service.return_value.getRobotConfig.return_value.value.return_value=[['Model Type','Body Version','Head Version'],['naoH25',revision,revision]]
        return qi

    def test_runtime_accepts_v4_without_touching_motion(self):
        qi=self.fake_qi('2.1.4.13')
        with patch.dict('sys.modules',{'qi':qi}):self.assertEqual(manager.check_runtime(),'2.1.4.13')
        self.assertIn(unittest.mock.call('ALSystem'),qi.Session.return_value.service.call_args_list)
    def test_owner_bootstrap_runtime_accepts_v5(self):
        qi=self.fake_qi('2.1.4.13','VERSION_50')
        with patch.dict('sys.modules',{'qi':qi}):self.assertEqual(manager.check_runtime(),'2.1.4.13')
        qi.Session.return_value.service.return_value.wakeUp.assert_not_called()
    def test_owner_bootstrap_runtime_accepts_v6_and_intermediate_2x(self):
        for version in ('2.5.5.5','2.8.7.4'):
            qi=self.fake_qi(version,'VERSION_60')
            with patch.dict('sys.modules',{'qi':qi}):self.assertEqual(manager.check_runtime(),version)
            qi.Session.return_value.service.return_value.wakeUp.assert_not_called()
    def test_unsupported_firmware_is_rejected_for_actual_runtime(self):
        from nao_profile import compatible_firmware
        for value in ('1.14.5','2.9.0','3.0.0','','2.x','2.0','not-a-version'):
            self.assertFalse(compatible_firmware(value))

    def test_runtime_rejects_android_nao_before_install(self):
        qi=self.fake_qi('2.9.5.172')
        with patch.dict('sys.modules',{'qi':qi}):
            with self.assertRaisesRegex(RuntimeError,'NAOqi 2.1-2.8'):manager.check_runtime()
        self.assertIn(unittest.mock.call('ALSystem'),qi.Session.return_value.service.call_args_list)

    def test_simulation_never_imports_real_robot_sdk(self):
        with patch.dict('sys.modules',{'qi':None}):self.assertEqual(manager.check_runtime(True),'simulation')

    def test_clean_exit_is_not_restarted(self):
        child=Mock();child.wait.return_value=0
        with patch.object(runner.signal,'signal'),patch.object(runner.subprocess,'Popen',return_value=child) as start:
            self.assertEqual(runner.run('test-token-file',simulate=True),0)
        self.assertEqual(start.call_count,1)
        self.assertIn('--simulate',start.call_args.args[0])

    def test_failure_retries_are_bounded_and_stay_simulated(self):
        child=Mock();child.wait.return_value=1
        with patch.object(runner.signal,'signal'),patch.object(runner.subprocess,'Popen',return_value=child) as start,patch.object(runner.time,'sleep'):
            self.assertEqual(runner.run('test-token-file',simulate=True),1)
        self.assertEqual(start.call_count,3)
        self.assertTrue(all('--simulate' in call.args[0] for call in start.call_args_list))

    def test_pid_one_is_never_owned(self):
        import io
        with patch('builtins.open',return_value=io.StringIO('1')):self.assertIsNone(manager.owned_pid())

    def test_unrelated_process_is_never_owned(self):
        import io
        with patch('builtins.open',side_effect=[io.StringIO('99'),io.BytesIO(b'/usr/bin/python\0another-service.py\0')]):
            self.assertIsNone(manager.owned_pid())

if __name__=='__main__':unittest.main()
