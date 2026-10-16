import sys
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nao/bridge'))
import telenao as tp
from woz import WoZ

class NativeArmBoundsTests(unittest.TestCase):
    def test_native_arm_targets_are_not_cut_by_the_old_application_envelope(self):
        robot=tp.Robot(True)
        native=[(-2.08,2.08),(-.31,1.32),(-2.08,2.08),(-1.54,-.035),(-1.82,1.82)]
        robot.hardware_limits[2:7]=native
        robot.hardware_limits[7:12]=[native[0],(-1.32,.31),native[2],(.035,1.54),native[4]]
        robot.set_motion_limit('range',True)
        self.assertEqual(robot.limits[2:12],robot.hardware_limits[2:12])
        target=list(robot.previous);target[2:7]=[-2.07,1.31,2.07,-1.53,1.81]
        target[7:12]=[-2.07,-1.31,-2.07,1.53,-1.81]
        with patch.object(tp,'clock',return_value=robot.armed_at+10):robot.apply(target,[0,0,0],.02)
        self.assertEqual(robot.previous[2:12],target[2:12])
        with self.assertRaises(ValueError):robot.set_motion_limit('range',False)
        robot.set_motion_limit('range',True)
        self.assertEqual(robot.limits[2:12],robot.hardware_limits[2:12])
        self.assertEqual(robot.limits[0],(-1.,1.));self.assertTrue(robot.speed_limited)
    def test_targets_beyond_hardware_bounds_are_still_clamped(self):
        robot=tp.Robot(True);target=list(robot.previous)
        for i in range(2,12):target[i]=100.
        with patch.object(tp,'clock',return_value=robot.armed_at+10):robot.apply(target,[0,0,0],.02)
        self.assertEqual(robot.previous[2:12],[p[1] for p in robot.hardware_limits[2:12]])
        self.assertEqual(robot.base,[0.,0.,0.])
    def test_status_exports_native_arm_bounds_and_compact_keeps_them(self):
        service=Mock(port=9570);service.state=tp.State(tp.Robot(True));service.video_diagnostics=[{}, {}, {}]
        with patch('woz.socket.socket'):woz=WoZ(service,tp.clock)
        try:
            service.state.robot.hardware_limits[3]=(-.31,1.32)
            status=woz.status();self.assertEqual(status['native_arm_limits']['LShoulderRoll'],[-.31,1.32])
            self.assertEqual(len(status['native_arm_limits']),10)
            self.assertNotIn('HeadYaw',status['native_arm_limits'])
            if hasattr(tp,'compact_status'):self.assertEqual(tp.compact_status(status)['native_arm_limits'],status['native_arm_limits'])
        finally:woz.audio_socket.close()
