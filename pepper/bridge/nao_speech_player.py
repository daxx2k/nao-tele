"""Arm-only derivatives read from the owner's installed NAO conversation resources.
No full behavior is executed, and no proprietary animation data is bundled.
"""
import math
import os
import xml.etree.ElementTree as ET
from speech_player25 import ClipFuture

PATHS=tuple('telenao-speaking/BodyTalk_%d'%n for n in (4,6,8))
ROOT='/home/nao/.local/share/PackageManager/apps/animations/Stand/BodyTalk/Speaking'

def finite(value):return not (math.isnan(value) or math.isinf(value))
def tag(node):return node.tag.rsplit('}',1)[-1]
def read_clip(path,allowed):
    document=ET.parse(path).getroot()
    timeline=next(e for e in document.iter() if tag(e)=='Timeline')
    fps=float(timeline.attrib['fps'])
    if not finite(fps) or not 1<=fps<=120:raise ValueError('Invalid animation frame rate')
    curves={}
    for curve in document.iter():
        name=curve.attrib.get('actuator')
        if tag(curve)!='ActuatorCurve' or name not in allowed or curve.attrib.get('mute')=='1':continue
        if curve.attrib.get('unit','0')!='0':raise ValueError('Unknown joint angle unit')
        keys=[]
        for key in curve:
            if tag(key)!='Key':continue
            stamp=float(key.attrib['frame'])/fps;angle=math.radians(float(key.attrib['value']))
            if not finite(stamp) or not finite(angle) or not 0<stamp<=10:raise ValueError('Invalid native keyframe')
            keys.append((stamp,angle))
        keys.sort()
        if not keys or any(b[0]<=a[0] for a,b in zip(keys,keys[1:])):raise ValueError('Invalid keyframe order')
        if name in curves:raise ValueError('Duplicate joint curve')
        curves[name]=keys
    if not curves:raise ValueError('No arm-only native curves')
    return curves

class NativeClip(object):
    def __init__(self,player,curves):
        self.player=player;self.curves=curves;self.names=sorted(curves)
        self.capture=player.robot.motion.getAngles(self.names,True,_async=True)
        self.began=player.clock();self.play=None;self.cancelled=False
    def cancel(self):
        self.cancelled=True
        if self.play is not None:self.play.cancel()
        else:self.capture.cancel()
    def isFinished(self):
        if self.play is not None:return self.play.isFinished()
        if self.cancelled:return self.capture.isFinished()
        if not self.capture.isFinished():
            if self.player.clock()-self.began>.5:raise RuntimeError('NAO speech pose read timed out')
            return False
        measured=list(self.capture.value(0))
        if len(measured)!=len(self.names) or any(not finite(v) for v in measured):raise ValueError('Invalid measured arm pose')
        robot=self.player.robot;bounded={};speed={};scale=1.;blend=2.
        for name,pose in zip(self.names,measured):
            i=self.player.indices[name];lo,hi=robot.limits[i]
            hwlo,hwhi=robot.hardware_limits[i]
            if not hwlo-.02<=pose<=hwhi+.02:raise ValueError('Measured arm pose outside hardware limits')
            bounded[name]=[(t,min(hi,max(lo,v))) for t,v in self.curves[name]]
            speed[name]=min(.6,robot.hardware_speed[i])
            if not finite(speed[name]) or speed[name]<=0:raise ValueError('Invalid arm speed cap')
            blend=max(blend,abs(bounded[name][0][1]-pose)/speed[name]+.1)
            for (t0,a0),(t1,a1) in zip(bounded[name],bounded[name][1:]):
                scale=max(scale,abs(a1-a0)/(t1-t0)/speed[name])
        angles=[];times=[]
        for name,pose in zip(self.names,measured):
            angles.append([pose]+[v for t,v in bounded[name]])
            times.append([.05]+[blend+t*scale for t,v in bounded[name]])
        if max(t[-1] for t in times)>12.:raise ValueError('Native arm gesture exceeds bounded duration')
        future=robot.motion.angleInterpolation(self.names,angles,times,True,_async=True)
        self.play=ClipFuture(robot.motion,self.names,future)
        return self.play.isFinished()
    def value(self,timeout=0):
        if self.play is None:
            if self.cancelled:return None
            raise RuntimeError('NAO arm gesture has not started')
        return self.play.value(timeout)

class SpeechPlayerNao(object):
    def __init__(self,robot,names,clock,root=ROOT):
        self.robot=robot;self.clock=clock;self.indices={n:i for i,n in enumerate(names)}
        self.clips={};self.errors={}
        allowed=set(names[2:12])
        for alias in PATHS:
            try:self.clips[alias]=read_clip(os.path.join(root,alias.rsplit('/',1)[-1],'behavior.xar'),allowed)
            except Exception as exc:self.errors[alias]=str(exc)
        self.available=len(self.clips)==len(PATHS)
    def run(self,path,_async=True):
        if not self.available or path not in self.clips:raise ValueError('Native NAO arm clip unavailable')
        return NativeClip(self,self.clips[path])
