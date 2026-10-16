# TeleNao

[![Buy me a coffee](https://img.shields.io/badge/Buy_me_a_coffee-Support_my_projects-FFDD00?logo=buymeacoffee&logoColor=000000)](https://buymeacoffee.com/daxx2k)

Control a NAO humanoid from Meta Quest: mirror your head, arms and hands, see through its two cameras, walk with the controllers, and speak through the robot. TeleNao also offers a desktop operator console for speech, LEDs and native posture presets.

Standalone NAO app with Android application ID `it.telenao.quest`, private settings and a robot service. Origin attribution is retained in NOTICE.

## Download

Experimental release **0.1.25-nao-test**. Use with an attentive operator and space around the robot.

| Package | Download |
|---|---|
| Quest app | [TeleNao-Quest.apk](https://github.com/daxx2k/nao-tele/releases/download/v0.1.25-nao-test/TeleNao-Quest.apk) |
| APK, installer and instructions | [Installation bundle](https://github.com/daxx2k/nao-tele/releases) |
| Source bundle and checksums | [Release assets](https://github.com/daxx2k/nao-tele/releases) |

## Arm mapping and appearance

Version **0.1.25-nao-test** includes the arm solver with full shoulder quadrants and live NAO joint limits. Arm elevation uses OpenXR gravity and shoulder heading instead of the estimated hip-to-spine tilt. The operator confirmed that forward arm alignment is now correct on the tested NAO. This does not confirm every pose or another NAO generation. Speed caps, walking, posture checks, STOP and gradual engagement are unchanged.

Select LEDs directly on the illustrated body: eyes, either ear, the top of the head, torso or either foot. Corner marks show the selected lights; choose a colour or intensity from the swatches below. Ears support blue brightness and the head supports white brightness. Text selector buttons are removed.

## Compatibility

Targets **NAO H25 v4, v5 and v6**, using the native Python qi/Pillow environment on NAOqi **2.1 through 2.8**. CONNECT tries the robot's available Python interpreters and preserves its SDK environment variables. There is no v4-only restriction.

| Generation | Hardware revision | Status |
|---|---|---|
| V4 | VERSION_40 | Live hardware evidence on NAOqi 2.1.4.13 |
| V5 | VERSION_50 | Enabled; physical confirmation pending |
| V6 | VERSION_60 | Enabled, including NAOqi 2.8; physical confirmation pending |

The bridge also accepts replacement-head combinations within these generations, checks H25 body type and reads live joint limits. Firmware, required services and a functioning qi/Pillow environment are checked before the service becomes available; a successful compatibility check never starts motion. See [Aldebaran model detection](https://fileadmin.cs.lth.se/robot/nao/doc/family/body_type.html) and [NAOqi API changes through 2.8](https://app.osrw.de/NAO/aldeb-doc-2.8.7.4/news/naosummary/api_nao.html).

Requires owner SSH access and a reachable network connection between NAO and Quest. CONNECT installs the Python bridge in `/home/nao/telenao`, without upgrading firmware or creating a boot-time service. Direct PC Ethernet helps setup but does not by itself connect Quest to the robot.

## Features and controls

- Head, arm and wrist tracking with NAO geometry and joint bounds; triggers close the hands. Direct mapping after gentle initial engagement, within hardware and speed limits.
- START requires fresh tracking. If NAO is crouched, seated or below standing height, it first requests native StandInit at speed 1.0 (100%); telepresence engages only after standing is confirmed. A + X starts/pauses; B stops.
- Native StandInit, Stand, Sit and Crouch presets in Motion, selectable during telepresence. Mapping pauses automatically; standing presets resume through fresh calibration, while Sit/Crouch stay paused.
- Left stick moves forward/backward and sideways. Right stick left/right turns; up/down adjusts standing height within a small bounded range. Centred sticks do not request walking.
- Both RGB cameras can run together at 5 requested frames/s each. A single camera requests 30 frames/s. A disarmed v4 test delivered about 15 frames/s at 160 x 120; performance depends on the robot and network.
- Remote voice, robot TTS, English/Italian phrases, offline Cori/Piper synthesis on Quest, microphone listening and volume.
- Eyes, chest and feet RGB LEDs; ears and head intensity controls. Native arm-only speech gestures are off by default.
- Left/right kicks use isolated original timelines from the installed Soccer package. Hello, Wave, Dance and Tai Chi run through their original installed NAOqi behaviors. Availability depends on packages installed on the robot; no proprietary timelines are bundled. B cancels; standing completion resumes through the normal START flow.
- Battery, temperature and motion information, movable panels, saved layouts, discovery and a connection screen without scrolling. The bottom grab handle and pin stay visible. A wide Appearance panel below the cameras and operator controls shows enlarged head, torso and foot crops of the approved NAO illustration and mirrors the saved LED colour and brightness selections; it does not read live robot LED state.

Motion includes a saved **Response: Smooth / Balanced / Quick** setting. It changes the acceleration of walking and rotation, not the 50% command cap or upper-body tracking. Balanced is the default. Centred sticks and STOP still stop promptly through native stopMove. On the right stick, the dominant axis selects turning or continuous height; small vertical deviations during a turn do not trigger crouching.

All joystick axes are capped at 50% normalized input; translation diagonals share that cap, with a 6 cm maximum forward-step setting. These limits do not guarantee actual physical speed or step length. A walking or turning request restores lowered standing height first. The gait stays stopped until torso sensors confirm standing height; releasing the stick prevents any deferred step.

Control, video and motion use separate connections. Brief command interruptions may recover an already armed session only with fresh tracking, centred sticks and a standing robot. Explicit STOP, tracking loss and full reconnection require START again. Temperature telemetry remains visible. TeleNao adds no temperature-based veto to START or posture presets; native NAOqi motor protections remain active.

## Setup and build

See [Quick start](docs/QUICKSTART.md), [Help](docs/HELP.md) and [Build](docs/BUILD.md). Install the APK with ADB, open connection settings, enter your robot address and SSH credentials, CONNECT, then Open VR. The optional installer also installs the offline Cori voice engine after verifying its download checksum.

Build with `tools/build.ps1 -Target Quest`; output: `dist/TeleNao-Quest.apk`. CONNECT deploys the bundled bridge over SSH.

The application, Java packages, native library and Python bridge use NAO naming.

## Privacy

Repository and release packages exclude robot passwords, pairing tokens, personal network addresses, recordings and device captures. Passwords are stored on Quest using Android Keystore encryption; pairing information remains in private app storage. Setup checks SSH host keys. Never commit local settings, signing keys or diagnostic captures.

Run `python tools/privacy_check.py --apks` before publication. See [Security](SECURITY.md) and the third-party notices included in the source.

## Validation and licence

Experimental port: builds, regressions, audible voice confirmation and disarmed camera/network checks do not establish physical tracking accuracy or gait stability. See [Validation](docs/VALIDATION.md). V5/V6 physical validation remains pending.

Apache-2.0, retaining upstream and third-party notices. Robot firmware and SDK components retain their own licences.
