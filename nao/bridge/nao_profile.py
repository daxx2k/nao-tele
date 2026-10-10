"""NAO H25 v4/v5/v6 on NAOqi 2.x; native postures and guarded walking."""
import numbers
LOWER_JOINTS=['LHipYawPitch','LHipRoll','LHipPitch','LKneePitch','LAnklePitch','LAnkleRoll',
              'RHipYawPitch','RHipRoll','RHipPitch','RKneePitch','RAnklePitch','RAnkleRoll']
HEAD_PITCH_LIMITS=(-.25,.20)
POSTURES=('StandInit','Stand','Sit','Crouch')
POSTURE_SPEED=.5
COMPATIBLE_REVISIONS=('VERSION_40','VERSION_50','VERSION_60')

def compatible_firmware(version):
    try:
        parts=str(version).split('.')
        return len(parts)>=2 and parts[0]=='2' and parts[1].isdigit() and 1<=int(parts[1])<=8
    except (TypeError,ValueError):return False

def check_posture_temperature(memory):
    """Use the robot's native thermal alarm; never override motor protection."""
    joints=['HeadYaw','HeadPitch','LShoulderPitch','LShoulderRoll','LElbowYaw',
            'LElbowRoll','LWristYaw','LHand','RShoulderPitch','RShoulderRoll',
            'RElbowYaw','RElbowRoll','RWristYaw','RHand']+LOWER_JOINTS
    # RHipYawPitch shares LHipYawPitch's physical actuator on H25.
    joints=[joint for joint in joints if joint!='RHipYawPitch']
    keys=['Device/SubDeviceList/'+joint+'/Temperature/Sensor/Status' for joint in joints]
    values=memory.getListData(keys,_async=True).value(2000)
    if len(values)!=len(keys):raise RuntimeError('Cannot verify motor temperatures')
    hot=[]
    for joint,value in zip(joints,values):
        if not isinstance(value,numbers.Real) or value not in (0,1,2,3):
            raise RuntimeError('Cannot verify motor temperature: '+joint)
        if value>0:hot.append(joint+' (status '+str(int(value))+')')
    if hot:raise RuntimeError('Motor thermal protection active: '+', '.join(hot)+'. Wait for cooling before posture changes')

def validate_robot(session,version=None):
    if version is None:version=session.service('ALSystem').systemVersion(_async=True).value(3000)
    if not compatible_firmware(version):
        raise RuntimeError('Requires the NAOqi 2.1-2.8 Python qi/Pillow runtime; found '+str(version))
    config=session.service('ALMotion').getRobotConfig(_async=True).value(3000)
    info=dict(zip(config[0],config[1]))
    if info.get('Model Type')!='naoH25':
        raise RuntimeError('Requires NAO H25 with legs, wrists and hands; found '+str(info.get('Model Type')))
    # Accept either compatible revision independently: replacement heads may
    # differ from the body. Live joint limits are read from ALMotion on startup.
    if info.get('Body Version') not in COMPATIBLE_REVISIONS or info.get('Head Version') not in COMPATIBLE_REVISIONS:
        raise RuntimeError('NAO H25 v4/v5/v6 revisions accepted; unverified head/body revisions: '+str(info.get('Head Version'))+'/'+str(info.get('Body Version')))
    return str(version)
