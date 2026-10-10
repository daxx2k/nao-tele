"""NAO v4 H25 on NAOqi 2.1; native postures and guarded walking."""
import numbers
LOWER_JOINTS=['LHipYawPitch','LHipRoll','LHipPitch','LKneePitch','LAnklePitch','LAnkleRoll',
              'RHipYawPitch','RHipRoll','RHipPitch','RKneePitch','RAnklePitch','RAnkleRoll']
HEAD_PITCH_LIMITS=(-.25,.20)
POSTURES=('StandInit','Stand','Sit','Crouch')
POSTURE_SPEED=.5

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
        if value>0:hot.append(joint)
    if hot:raise RuntimeError('Motors too hot: '+', '.join(hot)+'. Wait for cooling before posture changes')

def validate_robot(session,version=None):
    if version is None:version=session.service('ALSystem').systemVersion(_async=True).value(3000)
    if not str(version).startswith('2.1.'):
        raise RuntimeError('Requires NAO v4 NAOqi 2.1; found '+str(version))
    config=session.service('ALMotion').getRobotConfig(_async=True).value(3000)
    info=dict(zip(config[0],config[1]))
    if info.get('Model Type')!='naoH25' or info.get('Body Version')!='VERSION_40' or info.get('Head Version')!='VERSION_40':
        raise RuntimeError('Requires NAO v4 H25 head and body')
    return str(version)
