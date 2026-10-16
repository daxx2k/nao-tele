# TeleNao controls and help

Install TeleNao-Quest.apk on Quest 3. It uses its own application package and private settings.
CONNECT installs/starts the NAO head service using the owner SSH credentials; no tablet is needed.

1. Choose a posture any time: StandInit/Stand to stand, Sit to sit, Crouch to crouch. The app pauses tracking during the native movement. Standing completion resumes through START; seated/crouched completion remains paused.
2. Hold A + X or use START to calibrate and engage head/arms/hands gently.
3. Once standing and awake, hold the existing grip deadman and use the sticks to walk/turn.
4. B stops. Brief command interruptions have guarded recovery; explicit STOP, tracking loss and full reconnection require START again.

Postures are whole-body movements. START restores StandInit when NAO is not already standing at usable torso height, then calibrates and engages upper-body tracking. B cancels the stand-up.
Forward/backward, sideways and rotation commands are capped at 50% normalized input. Translation diagonals share that cap. The maximum forward-step setting remains 6 cm. Actual step length varies with stick input. Torso mirroring is excluded. The Animations panel offers installed NAO Hello, Wave, left/right kicks, Dance and Tai Chi. B cancels. Standing completion resumes through START; fresh tracking and centred sticks are required.
Exit stops the service and leaves autonomous life disabled.
After confirmed STOP and service shutdown, Exit returns to Quest Home and removes the app task. If the robot was never connected, Exit closes locally. If the connection is lost or STOP cannot be confirmed, **Close VR studio only** closes the headset app without claiming the robot service stopped; reconnect before using START again.
Physical preset, gait, STOP and tracking validation must be supervised.

Motion includes a saved **Response: Smooth / Balanced / Quick** setting. It changes the acceleration of walking and rotation, not the 50% command cap or upper-body tracking. Balanced is the default. Centred sticks and STOP still stop promptly through native stopMove. On the right stick, the dominant axis selects turning or continuous height; small vertical deviations during a turn do not trigger crouching.

The bottom grab handle and pin are always visible. A walking request while lowered first restores standing height and waits for torso sensor confirmation before any gait command.


## Appearance

Point and click directly on the body illustration to select eyes, ears, the top of the head, torso or feet, then choose a swatch below. Corner marks identify the selection. Both ears select the same ear LED group, and both feet select the same foot group. Ears change blue brightness; the head changes white brightness. Eyes, chest and feet support RGB colours. Selecting a body part alone does not send a colour command or move the robot.


## External power indicator

A blue plug next to the battery means the robot reports its power supply connected. It is separate from the charging flag: a connected power supply does not necessarily mean active battery charging. The indicator hides when telemetry is stale or the firmware supplies no usable signal. It is never inferred from battery percentage. Older battery firmware may infer plug status itself; the app displays the robot report.
