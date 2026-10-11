"""Bounded, continuous torso-height reference; centred stick holds its height."""
import math
class NaoHeight(object):
    def __init__(self):self.pose=None;self.ceiling=None;self.recovering=False;self.verify_at=0.
    def arm(self,pose,resume=False):
        if len(pose)!=6 or any(math.isnan(v) or math.isinf(v) for v in pose):raise ValueError('Invalid torso position')
        self.pose=list(pose);self.recovering=False;self.verify_at=0.
        if not resume or self.ceiling is None:self.ceiling=pose[2]
        self.floor=max(.26,self.ceiling-.04)
        if self.floor>self.ceiling:raise ValueError('Torso too low for standing height control')
    def target(self,axis,dt):
        if self.pose is None or axis==0:return None
        z=max(self.floor,min(self.ceiling,self.pose[2]+axis*.025*min(.05,max(0.,dt))))
        if abs(z-self.pose[2])<.00001:return None
        self.pose[2]=z
        return list(self.pose)
    def lowered(self):return self.pose is not None and self.ceiling-self.pose[2]>.002

    def restore_for_walking(self):
        if self.pose is None:return None
        if self.lowered():self.recovering=True
        if not self.recovering:return None
        self.pose[2]=self.ceiling
        return list(self.pose)
    def confirm_standing_height(self,measured,standing=True):
        if len(measured)!=6 or any(math.isnan(v) or math.isinf(v) for v in measured):raise ValueError('Invalid standing height measurement')
        if self.recovering and standing and measured[2]>=self.ceiling-.004 and abs(measured[3])<.2 and abs(measured[4])<.2:
            self.recovering=False
