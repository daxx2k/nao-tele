"""NAO H25 v4/v5/v6 on NAOqi 2.x; native postures and guarded walking."""
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
