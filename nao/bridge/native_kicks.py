"""Read allowlisted motion timelines from the owner's installed NAO packages.
No proprietary keyframes or behavior data are bundled.
Kicks use their isolated motion timelines; other clips run through NAOqi behavior management.
"""
import math
import os
import xml.etree.ElementTree as ET
ROOT='/home/nao/.local/share/PackageManager/apps/soccer-demonstration/behavior.xar'
BOXES={'kick_left':'LShoot','kick_right':'RShoot','hello':'root','wave':'Wave01_Nao_Standing','dance':'root','taichi':'TaiChiChuan'}
FILES={'kick_left':ROOT,'kick_right':ROOT,'hello':'/home/nao/.local/share/PackageManager/apps/animations/Stand/Emotions/Neutral/Hello_1/behavior.xar','wave':'/home/nao/.local/share/PackageManager/apps/dialog_move_hands/animations/Wave01/behavior.xar','dance':'/home/nao/.local/share/PackageManager/apps/animations/Stand/Waiting/FunnyDancer_1/behavior.xar','taichi':'/home/nao/.local/share/PackageManager/apps/taichi-dance-free/behavior.xar'}
BEHAVIORS={'hello':'animations/Stand/Emotions/Neutral/Hello_1','wave':'dialog_move_hands/animations/Wave01','dance':'animations/Stand/Waiting/FunnyDancer_1','taichi':'taichi-dance-free'}
JOINTS=set(('HeadYaw HeadPitch LShoulderPitch LShoulderRoll LElbowYaw LElbowRoll LWristYaw LHand RShoulderPitch RShoulderRoll RElbowYaw RElbowRoll RWristYaw RHand LHipYawPitch LHipRoll LHipPitch LKneePitch LAnklePitch LAnkleRoll RHipRoll RHipPitch RKneePitch RAnklePitch RAnkleRoll').split())
def tag(node):return node.tag.rsplit('}',1)[-1]
def read_kick(name,path=None):
    if name not in BOXES:raise ValueError('Unknown native kick')
    document=ET.parse(FILES[name] if path is None else path).getroot()
    boxes=[n for n in document.iter() if tag(n)=='Box' and n.get('name')==BOXES[name]]
    if len(boxes)!=1:raise ValueError('Native kick timeline missing or ambiguous')
    timelines=[n for n in boxes[0] if tag(n)=='Timeline' and n.get('enable')=='1']
    if len(timelines)!=1:raise ValueError('Native kick timeline unavailable')
    timeline=timelines[0];fps=float(timeline.get('fps'))
    if not 1<=fps<=120:raise ValueError('Invalid native frame rate')
    curves={}
    # Only direct actuator layers: never include nested script/behavior timelines.
    for layer in timeline:
        if tag(layer)!='ActuatorList':continue
        for curve in layer:
            if tag(curve)!='ActuatorCurve' or curve.get('mute')=='1':continue
            joint=curve.get('actuator')
            if joint not in JOINTS|set(['RHipYawPitch']) or joint in curves:raise ValueError('Invalid native joint curve')
            if joint in ('LHand','RHand'):
                if curve.get('unit') not in (None,'-1','0','1'):raise ValueError('Invalid hand unit')
            elif curve.get('unit') not in (None,'-1','0'):raise ValueError('Invalid angular unit')
            times=[];angles=[]
            for key in curve:
                if tag(key)!='Key':continue
                stamp=float(key.get('frame'))/fps;value=float(key.get('value'))
                if joint not in ('LHand','RHand'):value=math.radians(value)
                if math.isnan(stamp) or math.isinf(stamp) or not 0<stamp<=60:raise ValueError('Invalid native keyframe')
                if math.isnan(value) or math.isinf(value) or (times and stamp<=times[-1]):raise ValueError('Invalid native keyframe order')
                times.append(stamp);angles.append(value)
            if not times:raise ValueError('Empty native curve')
            curves[joint]=(angles,times)
    if 'RHipYawPitch' in curves:
        left=curves.get('LHipYawPitch');right=curves['RHipYawPitch']
        if left is None:raise ValueError('Missing primary coupled hip')
        primary=dict(zip(left[1],left[0]))
        # The physical hip is shared. The right alias may omit unchanged keys.
        if any(t not in primary or abs(v-primary[t])>.00001 for v,t in zip(right[0],right[1])):raise ValueError('Conflicting coupled hip curves')
        del curves['RHipYawPitch']
    if set(curves)!=JOINTS:raise ValueError('Incomplete native whole-body kick')
    names=sorted(curves)
    return names,[curves[n][0] for n in names],[curves[n][1] for n in names]
def available():
    found=[]
    for name in sorted(BOXES):
        try:
            if name in BEHAVIORS:
                if os.path.isfile(FILES[name]):found.append(name)
            else:read_kick(name);found.append(name)
        except (IOError,ValueError,TypeError,ET.ParseError):pass
    return found

class BehaviorFuture(object):
    def __init__(self,manager,path):
        self.manager=manager;self.path=path;self.cancel_future=None
        self.future=manager.runBehavior(path,_async=True)
    def cancel(self):
        if self.cancel_future is None:
            self.cancel_future=self.manager.stopBehavior(self.path,_async=True)
            self.future.cancel()
    def isFinished(self):
        return self.cancel_future.isFinished() if self.cancel_future is not None else self.future.isFinished()
    def value(self,timeout=0):return self.future.value(timeout)
