import io
import math
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pepper/bridge'))
from nao_speech_player import read_clip,NativeClip,SpeechPlayerNao

class Future:
    def __init__(self,value=None,done=True):self.result=value;self.done=done
    def isFinished(self):return self.done
    def value(self,timeout=0):return self.result
    def cancel(self):self.done=True

class NativeSpeechTests(unittest.TestCase):
    def xml(self,extra=''):
        return io.StringIO('<root><Timeline fps="25"/><ActuatorCurve actuator="LShoulderPitch" unit="0" mute="0"><Key frame="10" value="90"/><Key frame="25" value="30"/></ActuatorCurve>'+extra+'</root>')
    def test_extracts_only_requested_arm_channels_converts_degrees(self):
        extra='<ActuatorCurve actuator="HeadYaw" unit="0"><Key frame="10" value="90"/></ActuatorCurve><ActuatorCurve actuator="LHipPitch"><Key frame="10" value="60"/></ActuatorCurve>'
        curves=read_clip(self.xml(extra),{'LShoulderPitch'})
        self.assertEqual(set(curves),{'LShoulderPitch'});self.assertAlmostEqual(curves['LShoulderPitch'][0][1],math.pi/2)
    def test_muted_curves_are_not_executed(self):
        data=self.xml().getvalue().replace('mute="0"','mute="1"')
        with self.assertRaises(ValueError):read_clip(io.StringIO(data),{'LShoulderPitch'})
    def test_nonfinite_and_duplicate_keyframes_are_rejected(self):
        for a,b in [('value="90"','value="nan"'),('frame="25"','frame="10"')]:
            with self.assertRaises(ValueError):read_clip(io.StringIO(self.xml().getvalue().replace(a,b)),{'LShoulderPitch'})
    def player(self,pose=.2):
        p=Mock();p.indices={'LShoulderPitch':0};p.clock.return_value=0
        p.robot.limits=[(-1.,1.)];p.robot.hardware_limits=[(-2.,2.)];p.robot.hardware_speed=[.6]
        p.robot.motion.getAngles.return_value=Future([pose]);p.robot.motion.angleInterpolation.return_value=Future()
        return p
    def test_starts_from_measured_pose_clamps_native_curve_and_bounds_velocity(self):
        p=self.player();clip=NativeClip(p,{'LShoulderPitch':[(.4,1.5),(1.,-.7)]});clip.isFinished()
        args=p.robot.motion.angleInterpolation.call_args.args
        self.assertEqual(args[0],['LShoulderPitch']);self.assertEqual(args[1][0][0],.2)
        self.assertEqual(args[1][0][1],1.)
        for a0,a1,t0,t1 in zip(args[1][0],args[1][0][1:],args[2][0],args[2][0][1:]):self.assertLessEqual(abs(a1-a0)/(t1-t0),.600001)
    def test_cancellation_before_pose_read_never_commands_motors(self):
        p=self.player();p.robot.motion.getAngles.return_value=Future([.2],False)
        clip=NativeClip(p,{'LShoulderPitch':[(.4,.5)]});clip.cancel();self.assertTrue(clip.isFinished());p.robot.motion.angleInterpolation.assert_not_called()
    def test_cancellation_kills_only_clip_arm_resources(self):
        p=self.player();p.robot.motion.killTasksUsingResources.return_value=Future()
        clip=NativeClip(p,{'LShoulderPitch':[(.4,.5)]});clip.isFinished();clip.cancel()
        p.robot.motion.killTasksUsingResources.assert_called_once_with(['LShoulderPitch'],_async=True)
    def test_invalid_measured_pose_never_commands_motors(self):
        for value in [float('nan'),3.]:
            p=self.player(value);clip=NativeClip(p,{'LShoulderPitch':[(.4,.5)]})
            with self.assertRaises(ValueError):clip.isFinished()
            p.robot.motion.angleInterpolation.assert_not_called()
    def test_missing_native_resources_report_unavailable_without_motion(self):
        p=Mock();player=SpeechPlayerNao(p,['HeadYaw','HeadPitch','LShoulderPitch'],lambda:0,root='missing-test-resources')
        self.assertFalse(player.available);self.assertEqual(len(player.errors),3);self.assertEqual(p.motion.mock_calls,[])

if __name__=='__main__':unittest.main()
