import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pepper/bridge'))
from motion_dispatch import MotionDispatch,DrainFuture

class Future:
    def isFinished(self):return True
    def value(self,timeout=0):return True

class DispatchTests(unittest.TestCase):
    def test_submission_returns_while_sdk_is_blocked_and_queue_is_bounded(self):
        d=MotionDispatch();entered=threading.Event();release=threading.Event()
        def slow():entered.set();release.wait(2);return Future()
        try:
            first=d.submit(slow);self.assertTrue(entered.wait(1));self.assertFalse(first.isFinished())
            second=d.submit(lambda:Future());self.assertFalse(second.isFinished())
            self.assertLessEqual(d.jobs.qsize(),8)
            release.set();self.assertTrue(first.ready.wait(1));self.assertTrue(second.ready.wait(1))
            self.assertTrue(DrainFuture([first,second]).isFinished())
        finally:release.set();d.close()
    def test_stop_generation_prevents_old_queued_operations(self):
        d=MotionDispatch();operation=Mock(return_value=Future())
        try:
            # Hold the submission gate to exercise queued work deterministically.
            with d.gate:
                old=d.submit(operation);d.epoch+=1
            self.assertTrue(old.ready.wait(1));operation.assert_not_called()
            drain=DrainFuture([old]);self.assertTrue(drain.isFinished());drain.value()
            fresh=d.submit(operation);self.assertTrue(fresh.ready.wait(1));operation.assert_called_once()
        finally:d.close()

if __name__=='__main__':unittest.main()
