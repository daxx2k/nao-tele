import importlib.util
import pathlib
import threading
import socket
import json
import unittest
from unittest.mock import Mock, patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('exit_tp',ROOT/'nao/bridge/telenao.py')
tp=importlib.util.module_from_spec(spec);spec.loader.exec_module(tp)

class ExitNormalTests(unittest.TestCase):
    def make_service(self, simulate=True):
        service=tp.Service.__new__(tp.Service)
        robot=tp.Robot(True) if simulate else Mock(simulate=False,stop_pending={},motion_pending={},stop_error='')
        if not simulate:robot.life.getState.return_value.value.return_value='solitary'
        service.state=tp.State(robot)
        service.woz=Mock()
        service.closing=False;service.normal_exit=False;service.running=True
        service.exit_lock=threading.Lock()
        return service

    def test_exit_requires_deliberate_confirmation(self):
        s=self.make_service(False)
        for request in [{},{'confirmed':False},{'confirmed':'true'}]:
            with self.assertRaises(ValueError):s.return_to_normal(request)
        s.state.robot.life.setState.assert_not_called()

    def test_explicit_exit_releases_session_only_after_stop_and_normal_mode(self):
        s=self.make_service(False)
        events=[]
        s.state.robot.stop.side_effect=lambda:events.append('stop')
        s.state.robot.poll_stop.side_effect=lambda:events.append('ack')
        s.state.robot.life.setState.side_effect=lambda *a,**k:(events.append('normal') or Mock())
        s.state.session='pilot';s.state.peer='127.0.0.1';s.state.armed=True
        reply=s.return_to_normal({'confirmed':True})
        self.assertTrue(reply['normal_mode']);self.assertFalse(s.state.armed)
        self.assertEqual(reply['autonomous_life'],'solitary')
        self.assertIsNone(s.state.session);self.assertTrue(s.normal_exit)
        self.assertLess(events.index('stop'),events.index('ack'))
        self.assertLess(events.index('ack'),events.index('normal'))
        s.state.robot.life.setState.assert_called_once_with('solitary',_async=True)

    def test_interactive_state_after_handoff_is_accepted(self):
        s=self.make_service(False)
        s.state.robot.life.getState.return_value.value.return_value='interactive'
        reply=s.return_to_normal({'confirmed':True})
        self.assertTrue(reply['normal_mode']);self.assertEqual(reply['autonomous_life'],'interactive')

    def test_unconfirmed_autonomy_rolls_back_without_releasing_pilot(self):
        s=self.make_service(False);s.state.session='pilot'
        s.state.robot.life.getState.return_value.value.return_value='disabled'
        with self.assertRaisesRegex(RuntimeError,'not confirmed'):
            s.return_to_normal({'confirmed':True})
        self.assertFalse(s.normal_exit);self.assertFalse(s.closing)
        self.assertEqual(s.state.session,'pilot')
        self.assertEqual([c.args[0] for c in s.state.robot.life.setState.call_args_list],['solitary','disabled'])

    def test_handoff_query_failure_rolls_back(self):
        s=self.make_service(False)
        s.state.robot.life.getState.return_value.value.side_effect=RuntimeError('query failed')
        with self.assertRaisesRegex(RuntimeError,'query failed'):
            s.return_to_normal({'confirmed':True})
        self.assertFalse(s.normal_exit)
        self.assertEqual([c.args[0] for c in s.state.robot.life.setState.call_args_list],['solitary','disabled'])

    def test_synchronous_handoff_failure_attempts_rollback(self):
        s=self.make_service(False)
        def change(mode,**kw):
            if mode=='solitary':raise RuntimeError('handoff failed')
            return Mock()
        s.state.robot.life.setState.side_effect=change
        with self.assertRaisesRegex(RuntimeError,'handoff failed'):
            s.return_to_normal({'confirmed':True})
        self.assertFalse(s.closing);self.assertFalse(s.normal_exit)
        self.assertEqual([c.args[0] for c in s.state.robot.life.setState.call_args_list],['solitary','disabled'])

    def test_stop_during_autonomy_handoff_rolls_back(self):
        s=self.make_service(False)
        def change(mode,**kw):
            if mode=='solitary':s.state.stop_generation+=1
            return Mock()
        s.state.robot.life.setState.side_effect=change
        with self.assertRaisesRegex(RuntimeError,'handoff'):
            s.return_to_normal({'confirmed':True})
        self.assertFalse(s.closing);self.assertFalse(s.normal_exit)
        self.assertEqual([c.args[0] for c in s.state.robot.life.setState.call_args_list],['solitary','disabled'])

    def test_stop_interrupts_unfinished_handoff(self):
        s=self.make_service(False);pending=Mock();pending.isFinished.return_value=False
        def change(mode,**kw):
            if mode=='solitary':s.state.stop_generation+=1;return pending
            return Mock()
        s.state.robot.life.setState.side_effect=change
        with self.assertRaisesRegex(RuntimeError,'handoff'):
            s.return_to_normal({'confirmed':True})
        pending.cancel.assert_called_once()
        s.state.robot.life.getState.assert_not_called()
        self.assertFalse(s.closing);self.assertFalse(s.normal_exit)

    def test_handoff_timeout_cancels_and_rolls_back(self):
        s=self.make_service(False);pending=Mock();pending.isFinished.return_value=False
        s.state.robot.life.setState.side_effect=[pending,Mock()]
        with patch.object(tp,'clock',side_effect=[0,0,9]):
            with self.assertRaisesRegex(RuntimeError,'timed out'):
                s.return_to_normal({'confirmed':True})
        pending.cancel.assert_called_once()
        self.assertFalse(s.normal_exit);self.assertFalse(s.closing)
        self.assertEqual([c.args[0] for c in s.state.robot.life.setState.call_args_list],['solitary','disabled'])

    def test_failed_rollback_still_attempts_stop_and_unblocks_exit(self):
        s=self.make_service(False)
        def change(mode,**kw):
            future=Mock()
            if mode=='solitary':s.state.stop_generation+=1
            else:future.value.side_effect=RuntimeError('rollback failed')
            return future
        s.state.robot.life.setState.side_effect=change
        with self.assertRaisesRegex(RuntimeError,'rollback failed'):
            s.return_to_normal({'confirmed':True})
        self.assertGreaterEqual(s.state.robot.stop.call_count,2)
        self.assertFalse(s.closing);self.assertFalse(s.normal_exit)

    def test_stop_failure_never_enables_autonomy(self):
        s=self.make_service(False);s.state.robot.stop_error='Stop failed'
        with self.assertRaises(RuntimeError):s.return_to_normal({'confirmed':True})
        s.state.robot.life.setState.assert_not_called()
        self.assertFalse(s.normal_exit);self.assertFalse(s.closing)

    def test_unfinished_stop_times_out_without_enabling_autonomy(self):
        s=self.make_service(False);s.state.robot.stop_pending={'base':Mock()}
        with patch.object(tp,'clock',side_effect=[0,6]):
            with self.assertRaises(RuntimeError):s.return_to_normal({'confirmed':True})
        s.state.robot.life.setState.assert_not_called()

    def test_disconnect_remains_disarmed_without_resuming_life(self):
        s=self.make_service(False)
        s.state.robot.restore=tp.Robot.restore.__get__(s.state.robot,tp.Robot)
        s.state.robot.restore()
        s.state.robot.life.setState.assert_not_called()

    def test_new_stop_cancels_exit(self):
        s=self.make_service(False)
        s.state.robot.poll_stop.side_effect=lambda:setattr(s.state,'stop_generation',s.state.stop_generation+1)
        with self.assertRaises(RuntimeError):s.return_to_normal({'confirmed':True})
        s.state.robot.life.setState.assert_not_called()

class ExitProtocolTests(unittest.TestCase):
    def test_operator_protocol_requires_confirmation_and_exits_after_ack(self):
        # Windows can reserve UDP ranges independently of TCP ephemeral ports.
        for attempt in range(20):
            reservations=[]
            try:
                reserve=socket.socket();reservations.append(reserve);reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
                for offset in (1,3):
                    udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);reservations.append(udp);udp.bind(('0.0.0.0',port+offset))
                break
            except OSError:
                if attempt==19:raise
            finally:
                for reserve in reservations:reserve.close()
        service=tp.Service('test-normal-exit-token',True,port)
        server,client=socket.socketpair();client.settimeout(2)
        worker=threading.Thread(target=service.control,args=(server,('127.0.0.1',0)))
        worker.start();reader=client.makefile('rb')
        try:
            client.sendall((json.dumps({'token':'test-normal-exit-token','role':'operator'})+'\n').encode())
            self.assertIn('observer',json.loads(reader.readline()))
            client.sendall((json.dumps({'cmd':'return_to_normal'})+'\n').encode())
            self.assertFalse(json.loads(reader.readline())['ok']);self.assertTrue(service.running)
            client.sendall((json.dumps({'cmd':'return_to_normal','confirmed':True})+'\n').encode())
            reply=json.loads(reader.readline())
            self.assertTrue(reply['normal_mode']);self.assertTrue(reply['service_stopping'])
            worker.join(1);self.assertFalse(worker.is_alive());self.assertFalse(service.running)
        finally:
            reader.close();client.close();server.close();service.running=False;service.udp.close();service.woz.audio_socket.close();worker.join(1)

if __name__=='__main__':unittest.main()
