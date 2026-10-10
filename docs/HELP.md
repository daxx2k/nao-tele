# TeleNao controls and help

Install TeleNao-Quest.apk on Quest 3. It is a separate app alongside TelePepper.
CONNECT installs/starts the NAO head service using the owner SSH credentials; no tablet is needed.

1. Choose a preset while control is stopped: StandInit/Stand to stand, Sit to sit, Crouch to crouch.
2. Hold A + X or use START to calibrate and engage head/arms/hands gently.
3. Once standing and awake, hold the existing grip deadman and use the sticks to walk/turn.
4. B stops; every connection/tracking timeout requires explicit START to re-arm.

Postures are whole-body movements. START alone prepares upper-body motors and does not stand the robot.
Forward/backward walking uses a 35% normalized speed cap and a 6 cm maximum forward-step setting. Lateral motion and rotation remain capped at 10%. Actual step length varies with stick input. Torso mirroring and Pepper animation clips are excluded.
Exit stops the service and leaves autonomous life disabled.
Physical preset, gait, STOP and tracking validation must be supervised.
