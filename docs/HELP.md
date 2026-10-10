# TeleNao controls and help

Install TeleNao-Quest.apk on Quest 3. It is a separate app alongside TelePepper.
CONNECT installs/starts the NAO head service using the owner SSH credentials; no tablet is needed.

1. Choose a preset while control is stopped: StandInit/Stand to stand, Sit to sit, Crouch to crouch.
2. Hold A + X or use START to calibrate and engage head/arms/hands gently.
3. Once standing and awake, hold the existing grip deadman and use the sticks to walk/turn.
4. B stops. Brief command interruptions have guarded recovery; explicit STOP, tracking loss and full reconnection require START again.

Postures are whole-body movements. START restores StandInit when NAO is not already standing at usable torso height, then calibrates and engages upper-body tracking. B cancels the stand-up.
Forward/backward, sideways and rotation commands are capped at 50% normalized input. Translation diagonals share that cap. The maximum forward-step setting remains 6 cm. Actual step length varies with stick input. Torso mirroring and Pepper animation clips are excluded.
Exit stops the service and leaves autonomous life disabled.
Physical preset, gait, STOP and tracking validation must be supervised.

Motion includes a saved **Response: Smooth / Balanced / Quick** setting. It changes the acceleration of walking and rotation, not the 50% command cap or upper-body tracking. Balanced is the default. Centred sticks and STOP still stop promptly through native stopMove. On the right stick, the dominant axis selects turning or continuous height; small vertical deviations during a turn do not trigger crouching.
