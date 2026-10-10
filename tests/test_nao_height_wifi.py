import sys
from pathlib import Path
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pepper/bridge'))
from nao_height import NaoHeight
from wifi_reconnect import WifiReconnect

class Future:
    def __init__(self,value=None,finished=True):self.result=value;self.finished=finished
    def isFinished(self):return self.finished
    def value(self,timeout=0):return self.result

class HeightWifiTests(unittest.TestCase):
    def test_height_is_continuous_centred_holds_and_other_axes_never_change(self):
        h=NaoHeight();h.arm([.02,.01,.31,0.,0.,.03])
        down=h.target(-.5,.04)
        self.assertAlmostEqual(down[2],.3095)
        self.assertEqual(down[:2]+down[3:],[.02,.01,0.,0.,.03])
        self.assertIsNone(h.target(0.,.05));self.assertEqual(h.pose,down)
        self.assertGreater(h.target(1.,.04)[2],down[2])
    def test_height_limits_and_resume_cannot_accumulate_deeper_crouches(self):
        h=NaoHeight();h.arm([0.,0.,.31,0.,0.,0.])
        for _ in range(1000):h.target(-1.,.05)
        self.assertAlmostEqual(h.pose[2],.27)
        h.arm(list(h.pose),True)
        for _ in range(1000):h.target(-1.,.05)
        self.assertAlmostEqual(h.pose[2],.27)
        for _ in range(1000):h.target(1.,.05)
        self.assertAlmostEqual(h.pose[2],.31);self.assertFalse(h.lowered())
    def test_bad_or_nonstanding_height_is_rejected(self):
        for z in [float('nan'),float('inf'),.2]:
            with self.assertRaises(ValueError):NaoHeight().arm([0.,0.,z,0.,0.,0.])
    def watcher(self,state='idle'):
        manager=Mock();manager.services.return_value=Future([[['Type','wifi'],['Favorite',True],['Autoconnect',True],['State',state],['ServiceId','saved-test']]])
        manager.connect.return_value=Future();now=[0.]
        return WifiReconnect(manager,lambda:now[0]),manager,now
    def test_wifi_only_reconnects_saved_idle_network_while_stopped(self):
        w,m,now=self.watcher();w.tick(False);m.services.assert_not_called()
        w.tick(True);w.tick(True);m.connect.assert_called_once_with('saved-test',_async=True)
        w.tick(True);now[0]=10.;w.tick(True);m.services.assert_called_once()
    def test_wifi_online_or_inflight_never_gets_reconnect_storm(self):
        for state in ['ready','online','association','configuration']:
            w,m,now=self.watcher(state);w.tick(True);w.tick(True);m.connect.assert_not_called()
        w,m,now=self.watcher();m.services.return_value=Future(finished=False)
        for _ in range(30):w.tick(True);now[0]+=1.
        m.services.assert_called_once();m.connect.assert_not_called()

if __name__=='__main__':unittest.main()
