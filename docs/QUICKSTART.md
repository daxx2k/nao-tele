# TeleNao quick start

Install TeleNao-Quest.apk on Quest 3. It uses its own application package and private settings.
CONNECT installs/starts the NAO head service using the owner SSH credentials; no tablet is needed.

1. Choose a posture any time: StandInit/Stand to stand, Sit to sit, Crouch to crouch. The app pauses tracking during the native movement. Standing completion resumes through START; seated/crouched completion remains paused.
2. Hold A + X or use START to calibrate and engage head/arms/hands gently.
3. Once standing and awake, use the left stick to walk and right stick X to turn; right Y adjusts standing height.
4. B stops. Brief input timeouts can recover with stable tracking and centred sticks; explicit STOP, tracking loss and full reconnection require START.

Postures are whole-body movements. START restores StandInit when NAO is not already standing at a usable torso height, then calibrates and engages upper-body tracking. Telepresence stays paused throughout stand-up; B cancels.
Forward/backward, sideways and rotation commands are capped at 50% normalized input. Translation diagonals share that cap. The maximum forward-step setting remains 6 cm. Actual step length varies with stick input. Torso mirroring is excluded. The Animations panel offers installed NAO Hello, Wave, left/right kicks, Dance and Tai Chi. B cancels. Standing completion resumes through START; fresh tracking and centred sticks are required.
Explicit Exit confirms STOP, re-enables and verifies Autonomous Life, then stops the service and returns to Quest Home. NAO may resume installed autonomous activities. Disconnect, ordinary STOP and **Close VR studio only** never enable Autonomous Life. An unconfirmed handoff does not report successful exit. CONNECT updates the bundled robot bridge before use.
Physical preset, gait, STOP and tracking validation must be supervised.

Motion includes a saved **Response: Smooth / Balanced / Quick** setting. It changes the acceleration of walking and rotation, not the 50% command cap or upper-body tracking. Balanced is the default. Centred sticks and STOP still stop promptly through native stopMove. On the right stick, the dominant axis selects turning or continuous height; small vertical deviations during a turn do not trigger crouching.

The bottom grab handle and pin are always visible. A walking request while lowered first restores standing height and waits for torso sensor confirmation before any gait command.
