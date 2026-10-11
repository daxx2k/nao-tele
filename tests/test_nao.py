import importlib.util
import json
import math
from pathlib import Path
import socket
import threading
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('telenao',ROOT/'nao/bridge/telenao.py')
tp=importlib.util.module_from_spec(spec);spec.loader.exec_module(tp)
from nao_profile import validate_robot

class Future:
    def __init__(self,value=None,finished=True):self.result=value;self.finished=finished
    def isFinished(self):return self.finished
    def value(self,timeout=0):return self.result
    def cancel(self):self.finished=True

class NaoTests(unittest.TestCase):
    def robot(self):
        r=tp.Robot(True);r.arm();r.simulate=False;r.motion=Mock();r.posture=Mock();r.life=Mock()
        r.session=Mock();r.session.service.return_value.getListData.return_value=Future([0]*25)
        r.life.getState.return_value='disabled';r.motion.getStiffnesses.return_value=[1.]*14
        r.motion.getAngles.return_value=list(r.previous)
        r.motion.getPosition.return_value=Future([0.,0.,.31,0.,0.,0.])
        for name in ['setAngles','moveToward','stopMove']:
            getattr(r.motion,name).return_value=Future()
        r.posture.stopMove.return_value=Future();r.posture.getPosture.return_value=Future('StandInit');r.posture.getPostureFamily.return_value=Future('Standing');r.standing=True;r.standing_checked_at=tp.clock();r.walking_ready=True;r.walking_checked_at=tp.clock()
        return r
    def state(self):
        r=tp.Robot(True);r.arm();s=tp.State(r);s.session='pilot';s.peer='127.0.0.1';s.armed=True;return s
    def packet(self,s,**kw):
        p=dict(session='pilot',seq=1,sent=1000.,active=True,drive=True,angles=list(s.robot.previous),base=[1.,0.,0.]);p.update(kw);return p
    def test_arm_reads_upper_body_without_wake_or_leg_commands(self):
        r=self.robot();r.arm()
        r.motion.wakeUp.assert_not_called();r.life.setState.assert_not_called()
        r.motion.getAngles.assert_called_once_with(tp.NAMES,True)
        r.motion.setStiffnesses.assert_called_once_with(tp.NAMES,1.)
    def test_arm_refuses_unprepared_upper_motors(self):
        r=self.robot();r.motion.getStiffnesses.return_value=[0.]*14
        with self.assertRaises(RuntimeError):r.arm()
        r.motion.setAngles.assert_not_called()
    def test_arm_refuses_active_autonomy(self):
        r=self.robot();r.life.getState.return_value='solitary'
        with self.assertRaises(RuntimeError):r.arm()
    def test_arm_rejects_seated_crouched_and_unknown_posture(self):
        for family in ['Sitting','Crouching','Unknown']:
            r=self.robot();r.posture.getPostureFamily.return_value=Future(family)
            with self.assertRaisesRegex(RuntimeError,'requires NAO standing'):r.arm()
            r.motion.setAngles.assert_not_called();r.motion.setStiffnesses.assert_not_called()
    def test_active_control_stops_if_standing_is_lost_or_stale(self):
        for standing,age in [(False,0),(True,1)]:
            s=self.state();s.robot=self.robot();s.robot.standing=standing;s.robot.standing_checked_at=tp.clock()-age
            s.received=tp.clock();s.robot.apply=Mock()
            s.tick(tp.clock(),.02)
            self.assertFalse(s.armed);s.robot.apply.assert_not_called()
            self.assertIn('standing posture',s.fault)
    def test_torso_packet_never_dispatches_nao_joints(self):
        r=self.robot();r.apply(r.previous,[0.,0.,0.],.02,torso=[.2,.2])
        for call in r.motion.setAngles.call_args_list:
            self.assertTrue(set(call.args[0]).issubset(set(tp.NAMES)))
        self.assertFalse(r.torso_enabled)
    def test_walking_is_blocked_when_seated_or_stance_telemetry_stale(self):
        for ready,age in [(False,0),(True,1.)]:
            r=self.robot();r.walking_ready=ready;r.walking_checked_at=tp.clock()-age
            r.apply(r.previous,[1.,1.,1.],.02)
            self.assertEqual(r.base,[0.,0.,0.])
            r.motion.moveToward.assert_not_called()
    def test_walking_cap_bounds_diagonal_and_rotation(self):
        r=self.robot()
        for i in range(100):r.walking_checked_at=tp.clock();r.apply(r.previous,[1.,1.,1.],.02)
        self.assertLessEqual(math.hypot(*r.base[:2]),.50000001);self.assertLessEqual(abs(r.base[1]),.5);self.assertLessEqual(abs(r.base[2]),.5)
    def test_forward_drive_reaches_new_cap_and_passes_native_step_config(self):
        r=self.robot()
        for _ in range(100):
            r.walking_checked_at=tp.clock();r.apply(r.previous,[.5,0.,0.],.02)
        self.assertAlmostEqual(r.base[0],.5)
        self.assertEqual(r.motion.moveToward.call_args.args[3],[['MaxStepX',.06]])
    def test_sideways_and_turn_reach_half_scale_in_both_directions(self):
        for axis in (1,2):
            for sign in (-1,1):
                r=self.robot();target=[0.,0.,0.];target[axis]=sign*.5
                for _ in range(100):r.walking_checked_at=tp.clock();r.apply(r.previous,target,.02)
                self.assertAlmostEqual(r.base[axis],sign*.5)
                self.assertTrue(all(v==0 for i,v in enumerate(r.base) if i!=axis))
    def test_response_profiles_bound_acceleration_steering_and_reversal(self):
        first=[]
        for mode,(translation,rotation) in enumerate(tp.DRIVE_RESPONSE_ACCEL):
            r=self.robot();r.drive_response=mode
            for target in ([.5,0.,.5],[0.,-.5,-.5],[-.5,0.,.5]):
                before=list(r.base);r.walking_checked_at=tp.clock();r.apply(r.previous,list(target),.02)
                self.assertLessEqual(math.hypot(r.base[0]-before[0],r.base[1]-before[1]),translation*.02+1e-8)
                self.assertLessEqual(abs(r.base[2]-before[2]),rotation*.02+1e-8)
            first.append(abs(r.base[2]))
        self.assertLess(first[0],first[1]);self.assertLess(first[1],first[2])
    def test_every_response_profile_stops_on_centred_sticks(self):
        for mode in range(3):
            r=self.robot();r.drive_response=mode;r.base=[.2,.2,.4];r.base_sent=list(r.base)
            r.apply(r.previous,[0.,0.,0.],.02)
            self.assertEqual(r.base,[0.,0.,0.]);r.motion.stopMove.assert_called_with(_async=True)
    def test_response_setting_and_half_scale_axes_reach_robot(self):
        s=self.state();s.accept(self.packet(s,base=[0.,.5,-.5],drive_response=2),'127.0.0.1',1.)
        self.assertEqual(s.latest[1],[0.,.5,-.5]);self.assertEqual(s.robot.drive_response,2)
        for bad in (-1,3,True,1.5,'quick'):
            with self.assertRaises(ValueError):s.accept(self.packet(s,seq=2,drive_response=bad),'127.0.0.1',1.)
    def test_walking_raises_height_before_any_step_and_waits_for_sensor(self):
        r=self.robot();r.armed_at=tp.clock()-4;r.height.arm([0.,0.,.31,0.,0.,0.]);r.height.pose[2]=.275
        r.motion.setPositions.return_value=Future();r.motion.getPosition.return_value=Future([0.,0.,.275,0.,0.,0.])
        r.apply(r.previous,[.5,0.,0.],.02,height=-1.)
        self.assertTrue(r.height.recovering);self.assertEqual(r.base,[0.,0.,0.])
        self.assertAlmostEqual(r.motion.setPositions.call_args.args[2][2],.31);r.motion.moveToward.assert_not_called()
        r.apply(r.previous,[.5,0.,0.],.02);r.motion.moveToward.assert_not_called()
        r.height.verify_at=0.;r.motion.getPosition.return_value=Future([0.,0.,.31,0.,0.,0.])
        r.apply(r.previous,[.5,0.,0.],.02);r.apply(r.previous,[.5,0.,0.],.02)
        self.assertFalse(r.height.recovering)
        r.apply(r.previous,[.5,0.,0.],.02);r.motion.moveToward.assert_called_once()
    def test_height_sensor_alone_cannot_release_walking_before_standing_family(self):
        from nao_height import NaoHeight
        height=NaoHeight();height.arm([0.,0.,.31,0.,0.,0.]);height.pose[2]=.275
        height.restore_for_walking();height.confirm_standing_height([0.,0.,.31,0.,0.,0.],False)
        self.assertTrue(height.recovering)
        height.confirm_standing_height([0.,0.,.31,0.,0.,0.],True);self.assertFalse(height.recovering)
    def test_releasing_walk_during_height_restore_never_starts_gait(self):
        r=self.robot();r.armed_at=tp.clock()-4;r.height.arm([0.,0.,.31,0.,0.,0.]);r.height.pose[2]=.275
        r.motion.setPositions.return_value=Future();r.motion.getPosition.return_value=Future([0.,0.,.31,0.,0.,0.])
        r.apply(r.previous,[.5,0.,0.],.02)
        for _ in range(5):r.apply(r.previous,[0.,0.,0.],.02)
        r.motion.moveToward.assert_not_called();self.assertEqual(r.base,[0.,0.,0.])
    def test_deadman_release_sends_zero_immediately(self):
        r=self.robot();r.apply(r.previous,[1.,0.,0.],.02);r.apply(r.previous,[0.,0.,0.],.02)
        self.assertEqual(r.base,[0.,0.,0.]);r.motion.stopMove.assert_called_with(_async=True)
    def test_stop_brakes_and_cancels_preset_without_nao_torso(self):
        r=self.robot();r.motion.getAngles.return_value=Future(list(r.previous));r.stop();r.poll_stop();r.poll_stop()
        r.motion.stopMove.assert_called_once();r.posture.stopMove.assert_called_once()
        r.motion.getAngles.assert_called_once_with(tp.NAMES,True,_async=True)
        r.motion.setAngles.assert_called_once_with(tp.NAMES,r.previous,.1,_async=True)
    def test_stop_barrier_blocks_arm_until_native_acknowledgement(self):
        r=self.robot();r.posture.stopMove.return_value=Future(finished=False);r.motion.getAngles.return_value=Future(r.previous)
        r.stop()
        with self.assertRaises(RuntimeError):r.arm()
    def test_tracking_loss_holds_pose_without_auto_recovery_or_neutral(self):
        s=self.state();s.accept(self.packet(s,active=False,pause_reason='tracking'),'127.0.0.1',1.)
        self.assertFalse(s.armed);self.assertIsNone(s.relax_at);self.assertIsNone(s.recovery_until)
    def test_timeout_offers_bounded_recovery_for_an_active_pilot(self):
        s=self.state();s.tracking_valid=True;s.pause_for_timeout(1.)
        self.assertFalse(s.armed);self.assertEqual(s.recovery_until,6.)
    def test_body_yaw_never_moves_base_with_centred_joysticks(self):
        s=self.state();s.robot.apply=Mock();s.base_feedback=(0.,1.)
        s.accept(self.packet(s,base=[0.,0.,0.],auto_turn=True,body_yaw=.5),'127.0.0.1',1.)
        s.tick(1.01,.02)
        self.assertFalse(s.auto_turn);self.assertEqual(s.robot.apply.call_args.args[1],[0.,0.,0.])
    def test_height_packet_reaches_apply_without_nao_torso_assist(self):
        s=self.state();s.robot.apply=Mock()
        s.accept(self.packet(s,height=-.7,torso_assist=False),'127.0.0.1',1.)
        s.tick(1.01,.02)
        self.assertEqual(s.robot.apply.call_args.kwargs['height'],-.7)
    def test_centred_sticks_never_start_gait_and_release_stops_it(self):
        r=self.robot();r.armed_at=tp.clock()-4
        r.apply(r.previous,[0.,0.,0.],.02);r.motion.moveToward.assert_not_called()
        r.apply(r.previous,[1.,0.,0.],.02);r.motion.moveToward.assert_called_once()
        r.apply(r.previous,[0.,0.,0.],.02);r.motion.stopMove.assert_called_once()
        self.assertEqual(r.motion.moveToward.call_count,1)
    def test_recovery_requires_stable_input_and_stop_cancels_it(self):
        s=self.state();s.tracking_valid=True;s.pause_for_timeout(1.)
        s.recovery_since=1.1;s.received=1.5;s.robot.arm=Mock()
        s.maybe_recover(1.5);self.assertFalse(s.armed);s.robot.arm.assert_not_called()
        s.received=1.7;s.maybe_recover(1.7);self.assertTrue(s.armed);self.assertEqual(s.recovery_count,1)
        s.pause_for_timeout(2.);s.disarm('STOP');self.assertIsNone(s.recovery_until)
    def test_recovery_does_not_resume_with_displaced_sticks_or_invalid_stance(self):
        s=self.state();s.tracking_valid=True;s.pause_for_timeout(1.)
        s.accept(self.packet(s,sticks_neutral=False),'127.0.0.1',1.1)
        s.maybe_recover(1.7);self.assertFalse(s.armed)
        s.robot=self.robot();s.robot.posture.getPostureFamily.return_value=Future('Sitting')
        s.recovery_since=1.1;s.received=1.7;s.maybe_recover(1.7)
        self.assertFalse(s.armed);self.assertIsNone(s.recovery_until)
    def test_foreign_and_out_of_order_packets_cannot_command_motion(self):
        s=self.state();self.assertFalse(s.accept(self.packet(s,session='foreign'),'127.0.0.1',1.))
        self.assertTrue(s.accept(self.packet(s),'127.0.0.1',1.));self.assertFalse(s.accept(self.packet(s),'127.0.0.1',1.01))
    def test_nonfinite_packet_is_rejected(self):
        s=self.state();angles=list(s.robot.previous);angles[0]=float('nan')
        with self.assertRaises(ValueError):s.accept(self.packet(s,angles=angles),'127.0.0.1',1.)
    def test_joint_and_speed_limits_cannot_be_removed(self):
        for key in ['range','speed','base']:
            with self.assertRaises(ValueError):tp.Robot(True).set_motion_limit(key,False)
    def test_following_sends_latest_bounded_pose_and_unscaled_hand_aperture(self):
        r=self.robot();r.armed_at=tp.clock()-4
        target=list(r.previous);target[2]=.7;target[3]=.4;target[12]=0.;target[13]=1.
        r.apply(target,[0.,0.,0.],.02)
        self.assertEqual(r.previous,target)
        calls=r.motion.setAngles.call_args_list
        self.assertEqual(calls[1].args[1],target[2:12]);self.assertEqual(calls[1].args[2],.5)
        self.assertEqual(calls[2].args[1],[0.,1.]);self.assertEqual(calls[2].args[2],.6)
    def test_height_uses_native_cartesian_torso_and_excludes_walking(self):
        r=self.robot();r.height.arm([0.,0.,.31,0.,0.,0.]);r.armed_at=tp.clock()-4
        r.motion.setPositions.return_value=Future()
        r.apply(r.previous,[0.,0.,0.],.04,height=-1.)
        call=r.motion.setPositions.call_args
        self.assertEqual(call.args[0:2],('Torso',2));self.assertEqual(call.args[3:],(.2,63))
        self.assertLess(call.args[2][2],.31);self.assertEqual(r.base,[0.,0.,0.])
    def test_height_stop_captures_and_holds_measured_legs(self):
        r=self.robot();r.height.arm([0.,0.,.31,0.,0.,0.])
        r.motion.killTasksUsingResources.return_value=Future()
        r.motion.getAngles.side_effect=lambda names,*args,**kw:Future([0.]*len(names))
        r.stop();r.poll_stop();r.poll_stop()
        r.motion.killTasksUsingResources.assert_called_once()
        self.assertTrue(any('LKneePitch' in call.args[0] for call in r.motion.setAngles.call_args_list))
    def test_engagement_keeps_measured_pose_blend_and_active_targets_stay_bounded(self):
        r=self.robot();initial=list(r.previous);r.armed_at=tp.clock()
        target=[99.]*14;r.apply(target,[0.,0.,0.],.02)
        self.assertLess(max(abs(a-b) for a,b in zip(initial,r.previous)),.02)
        r.armed_at=tp.clock()-4;r.apply(target,[0.,0.,0.],.02)
        for i,value in enumerate(r.previous):self.assertLessEqual(value,r.limits[i][1])
    def test_nao_animation_and_speech_curves_are_unavailable(self):
        r=tp.Robot(True);self.assertFalse(r.speech_arms.available());self.assertEqual(r.available_animations,set())
        with self.assertRaises(ValueError):r.begin_animation('wave_left')
    def service(self):
        svc=tp.Service.__new__(tp.Service);svc.state=tp.State(tp.Robot(True));svc.spawn=Mock();return svc
    def test_preset_is_allowlisted_confirmed_and_can_pause_active_tracking(self):
        svc=self.service()
        for name,confirmed in [('StandInit',False),('StandZero',True),('arbitrary',True)]:
            with self.assertRaises(ValueError):svc.prepare_posture(name,confirmed)
        svc.state.armed=True
        svc.prepare_posture('Sit',True)
        self.assertFalse(svc.state.armed);self.assertTrue(svc.state.preparing)
        svc.spawn.assert_called_once_with(svc._prepare_posture,'Sit')
    def test_native_animation_accepts_active_pilot_and_stays_disarmed(self):
        svc=self.service();svc.state.armed=True
        svc.prepare_native_animation('kick_left',True)
        self.assertTrue(svc.state.preparing);self.assertFalse(svc.state.armed)
        svc.spawn.assert_called_once_with(svc._prepare_native_animation,'kick_left')
    def test_official_dance_runs_native_behavior_without_rewriting_joint_curves(self):
        svc=self.service();r=svc.state.robot=self.robot();svc.state.preparing=True
        r.life.getState.return_value=Future('disabled');r.motion.wakeUp.return_value=Future()
        r.posture.goToPosture.return_value=Future(True)
        manager=r.session.service.return_value;manager.runBehavior.return_value=Future()
        svc._prepare_native_animation('dance')
        manager.runBehavior.assert_called_once_with('animations/Stand/Waiting/FunnyDancer_1',_async=True)
        r.motion.angleInterpolation.assert_not_called();r.motion.getLimits.assert_not_called()
        self.assertFalse(svc.state.armed);self.assertFalse(svc.state.preparing)
    def test_native_animation_is_confirmed_allowlisted_and_not_overlapping(self):
        svc=self.service()
        for name,confirm in [('kick_left',False),('arbitrary',True)]:
            with self.assertRaises(ValueError):svc.prepare_native_animation(name,confirm)
        svc.state.preparing=True
        with self.assertRaises(ValueError):svc.prepare_native_animation('kick_right',True)
        svc.spawn.assert_not_called()
    def test_preset_dispatches_native_posture_without_arming(self):
        svc=self.service();svc.prepare_posture('Sit',True)
        self.assertTrue(svc.state.preparing);self.assertFalse(svc.state.armed)
        svc.spawn.assert_called_once_with(svc._prepare_posture,'Sit')
    def test_cancelled_preset_never_dispatches_next_operation(self):
        svc=self.service();r=svc.state.robot=self.robot();svc.state.prepare_cancelled=True
        svc._prepare_posture('StandInit')
        r.motion.wakeUp.assert_not_called();r.posture.goToPosture.assert_not_called();self.assertFalse(svc.state.preparing)
    def test_all_native_presets_use_full_speed_and_stay_disarmed(self):
        for name in ('StandInit','Stand','Sit','Crouch'):
            svc=self.service();r=svc.state.robot=self.robot();r.life.getState.return_value=Future('disabled')
            r.motion.setStiffnesses.return_value=Future();r.motion.wakeUp.return_value=Future()
            r.posture.goToPosture.return_value=Future(True);r.posture.getPosture.return_value=Future(name)
            svc._prepare_posture(name)
            r.posture.goToPosture.assert_called_once_with(name,1.0,_async=True)
            self.assertFalse(svc.state.armed);self.assertFalse(svc.state.preparing)
    def test_failed_native_posture_is_reported_and_stays_disarmed(self):
        svc=self.service();r=svc.state.robot=self.robot();r.life.getState.return_value=Future('disabled')
        r.motion.setStiffnesses.return_value=Future();r.posture.goToPosture.return_value=Future(False)
        svc._prepare_posture('Sit')
        self.assertIn('Preparation failed',svc.state.prepare_message);self.assertFalse(svc.state.armed)
    def test_postures_do_not_add_a_thermal_veto(self):
        for value in (1,2,3,None):
            svc=self.service();r=svc.state.robot=self.robot()
            r.session.service.return_value.getListData.return_value=Future([value]*25)
            r.life.getState.return_value=Future('disabled')
            r.motion.setStiffnesses.return_value=Future()
            r.posture.goToPosture.return_value=Future(True)
            r.posture.getPosture.return_value=Future('Sit')
            svc._prepare_posture('Sit')
            r.posture.goToPosture.assert_called_once_with('Sit',1.0,_async=True)
            r.session.service.return_value.getListData.assert_not_called()
            self.assertEqual(svc.state.prepare_message,'Posture Sit ready / press START')
            self.assertFalse(svc.state.armed)
    def test_start_stands_from_crouch_even_when_firmware_family_is_standing(self):
        svc=self.service();r=svc.state.robot=self.robot()
        r.life.getState.return_value=Future('disabled');r.posture.getPosture.return_value=Future('Crouch')
        r.motion.wakeUp.return_value=Future();r.posture.goToPosture.return_value=Future(True)
        svc._prepare_motion()
        r.posture.goToPosture.assert_called_once_with('StandInit',1.0,_async=True)
    def test_start_does_not_add_a_thermal_rejection(self):
        r=self.robot();r.session.service.return_value.getListData.return_value=Future([1]+[0]*24)
        r.arm()
        r.motion.setStiffnesses.assert_called_once_with(tp.NAMES,1.)
        r.session.service.return_value.getListData.assert_not_called()
    def test_start_preparation_stands_from_crouch_at_standard_speed(self):
        svc=self.service();r=svc.state.robot=self.robot()
        r.life.getState.return_value=Future('disabled')
        r.posture.getPostureFamily.side_effect=[Future('Crouching'),Future('Standing')]
        r.motion.getPosition.side_effect=[Future([0.,0.,.22,0.,0.,0.]),Future([0.,0.,.31,0.,0.,0.])]
        r.motion.wakeUp.return_value=Future();r.posture.goToPosture.return_value=Future(True)
        r.motion.setStiffnesses.return_value=Future()
        svc._prepare_motion()
        r.posture.goToPosture.assert_called_once_with('StandInit',1.0,_async=True)
        self.assertEqual(svc.state.prepare_message,'Posture ready.');self.assertFalse(svc.state.armed)
    def test_start_preparation_restores_low_torso_even_if_family_is_standing(self):
        svc=self.service();r=svc.state.robot=self.robot();r.life.getState.return_value=Future('disabled')
        r.motion.getPosition.side_effect=[Future([0.,0.,.23,0.,0.,0.]),Future([0.,0.,.31,0.,0.,0.])]
        r.motion.wakeUp.return_value=Future();r.posture.goToPosture.return_value=Future(True)
        r.motion.setStiffnesses.return_value=Future()
        svc._prepare_motion();r.posture.goToPosture.assert_called_once_with('StandInit',1.0,_async=True)
        self.assertEqual(svc.state.prepare_message,'Posture ready.')
    def test_start_preparation_skips_pose_if_already_standing(self):
        svc=self.service();r=svc.state.robot=self.robot();r.life.getState.return_value=Future('disabled')
        r.motion.setStiffnesses.return_value=Future()
        svc._prepare_motion();r.motion.wakeUp.assert_not_called();r.posture.goToPosture.assert_not_called()
        self.assertEqual(svc.state.prepare_message,'Posture ready.')
    def test_start_stand_failure_or_cancel_never_engages_control(self):
        for cancelled in (False,True):
            svc=self.service();r=svc.state.robot=self.robot();r.life.getState.return_value=Future('disabled')
            r.posture.getPostureFamily.return_value=Future('Crouching')
            r.motion.getPosition.return_value=Future([0.,0.,.22,0.,0.,0.])
            svc.state.prepare_cancelled=cancelled
            r.motion.wakeUp.return_value=Future();r.posture.goToPosture.return_value=Future(False)
            svc._prepare_motion();self.assertFalse(svc.state.armed)
            r.motion.setStiffnesses.assert_not_called()
            if cancelled:r.posture.goToPosture.assert_not_called()
            else:self.assertIn('could not reach StandInit',svc.state.prepare_message)
    def test_disconnect_cancellation_preserves_reason(self):
        svc=self.service();svc.state.preparing=True
        svc.state.disarm('Pilot disconnected')
        svc._prepare_posture('Stand')
        self.assertIn('Pilot disconnected',svc.state.prepare_message)
    def test_matching_firmware_on_another_robot_is_still_rejected(self):
        session=Mock();session.service.return_value.getRobotConfig.return_value.value.return_value=[['Model Type','Body Version','Head Version'],['Robot','VERSION_40','VERSION_40']]
        with self.assertRaises(RuntimeError):validate_robot(session,'2.1.4.13')
    def test_h25_v4_v5_v6_and_replacement_head_combinations_are_accepted(self):
        for head in ('VERSION_40','VERSION_50','VERSION_60'):
            for body in ('VERSION_40','VERSION_50','VERSION_60'):
                session=Mock();motion=session.service.return_value
                motion.getRobotConfig.return_value.value.return_value=[['Model Type','Body Version','Head Version'],['naoH25',body,head]]
                self.assertEqual(validate_robot(session,'2.1.4.13'),'2.1.4.13')
                motion.wakeUp.assert_not_called();motion.setAngles.assert_not_called()
    def test_partial_body_and_unknown_revisions_have_specific_diagnostics(self):
        for model,head,body,message in [('naoH21','VERSION_50','VERSION_50','Requires NAO H25'),('naoH25','VERSION_70','VERSION_70','unverified head/body'),('naoH25',None,'VERSION_50','unverified head/body')]:
            session=Mock();session.service.return_value.getRobotConfig.return_value.value.return_value=[['Model Type','Body Version','Head Version'],[model,body,head]]
            with self.assertRaisesRegex(RuntimeError,message):validate_robot(session,'2.1.4.13')
    def test_chest_rgb_uses_verified_native_channels_instead_of_broken_group_fade(self):
        leds=Mock();tp.WoZ.set_chest_color(leds,0x4388ff)
        leds.fadeRGB.assert_not_called()
        self.assertEqual(leds.setIntensity.call_args_list,[unittest.mock.call('ChestBoard/Led/Red/Actuator/Value',67/255.),unittest.mock.call('ChestBoard/Led/Green/Actuator/Value',136/255.),unittest.mock.call('ChestBoard/Led/Blue/Actuator/Value',1.)])
    def test_compact_status_preserves_stop_and_tracking_state_without_mutating_full_status(self):
        full={'armed':False,'motion_diagnostics':{'stop_generation':4,'tracking_valid':True,'stop_history':[1,2]},
              'telemetry':{'motion_ready':True,'joint_measured':[.123456]*14,'requested_joint_target':[0]*14},'robot_mono':1234.123456}
        compact=tp.compact_status(full)
        self.assertEqual(compact['motion_diagnostics']['stop_generation'],4)
        self.assertTrue(compact['motion_diagnostics']['tracking_valid']);self.assertTrue(compact['telemetry']['motion_ready'])
        self.assertEqual(len(compact['telemetry']['joint_measured']),14)
        self.assertIn('stop_history',full['motion_diagnostics']);self.assertNotIn('stop_history',compact['motion_diagnostics'])
        self.assertAlmostEqual(compact['robot_mono'],full['robot_mono'],places=4)
    def test_old_qi_transport_uses_disconnect_signal_flag(self):
        svc=self.service();svc.state.robot.simulate=False;svc.state.robot.connection_lost=False
        self.assertTrue(svc.check_robot_connection());svc.state.robot.connection_lost=True
        self.assertFalse(svc.check_robot_connection());self.assertFalse(svc.running)

if __name__=='__main__':unittest.main()
