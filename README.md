# TeleNao

Control a NAO humanoid from Meta Quest: mirror your head, arms and hands, see through its two cameras, walk with the controllers, and speak through the robot. TeleNao also offers a desktop operator console for speech, LEDs and native posture presets.

A separate app derived from [TelePepper](https://github.com/daxx2k/pepper-tele), with its own Android application ID (`it.telenao.quest`), settings and robot service.

## Download

Experimental release **0.1.10-naov4-test**. Use with an attentive operator and space around the robot.

| Package | Download |
|---|---|
| Quest app | [TeleNao-Quest.apk](https://github.com/daxx2k/nao-tele/releases/download/v0.1.10-naov4-test/TeleNao-Quest.apk) |
| APK, installer and instructions | [Installation bundle](https://github.com/daxx2k/nao-tele/releases) |
| Source bundle and checksums | [Release assets](https://github.com/daxx2k/nao-tele/releases) |

## Compatibility

Targets **NAO v4 H25 with NAOqi 2.1**, developed with NAOqi 2.1.4.13 and Quest 3.

**NAO v5 and v6 are possible future targets, awaiting testers.** V5 shares the NAOqi 2.1 platform; V6 normally uses NAOqi 2.8. Neither is validated or enabled by the installer. Model, firmware, Python runtime, cameras and motion limits need checking on real hardware before support is confirmed. The same Quest interface is intended to be retained where possible.

Requires owner SSH access and a reachable network connection between NAO and Quest. CONNECT installs the Python bridge in `/home/nao/telenao`, without upgrading firmware or creating a boot-time service. Direct PC Ethernet helps setup but does not by itself connect Quest to the robot.

## Features and controls

- Head, arm and wrist tracking with NAO geometry and joint bounds; triggers close the hands. Direct mapping after gentle initial engagement, within hardware and speed limits.
- START requires fresh tracking. If NAO is crouched, seated or below standing height, it first requests native StandInit at speed 0.5; telepresence engages only after standing is confirmed. A + X starts/pauses; B stops.
- Native StandInit, Stand, Sit and Crouch presets in Motion, while telepresence is stopped.
- Left stick moves forward/backward and sideways. Right stick left/right turns; up/down adjusts standing height within a small bounded range. Centred sticks do not request walking.
- Both RGB cameras can run together at 5 requested frames/s each. A single camera requests 30 frames/s. A disarmed v4 test delivered about 15 frames/s at 160 x 120; performance depends on the robot and network.
- Remote voice, robot TTS, English/Italian phrases, offline Cori/Piper synthesis on Quest, microphone listening and volume.
- Eyes, chest and feet RGB LEDs; ears and head intensity controls. Native arm-only speech gestures are off by default.
- Battery, temperature and motion information, movable panels, saved layouts, discovery and a connection screen without scrolling.

Motion includes a saved **Response: Smooth / Balanced / Quick** setting. It changes the acceleration of walking and rotation, not the 50% command cap or upper-body tracking. Balanced is the default. Centred sticks and STOP still stop promptly through native stopMove. On the right stick, the dominant axis selects turning or continuous height; small vertical deviations during a turn do not trigger crouching.

All joystick axes are capped at 50% normalized input; translation diagonals share that cap, with a 6 cm maximum forward-step setting. These limits do not guarantee actual physical speed or step length. Lowered standing height prevents walking until height is restored.

Control, video and motion use separate connections. Brief command interruptions may recover an already armed session only with fresh tracking, centred sticks and a standing robot. Explicit STOP, tracking loss and full reconnection require START again. Firmware protections remain active.

## Setup and build

See [Quick start](docs/QUICKSTART.md), [Help](docs/HELP.md) and [Build](docs/BUILD.md). Install the APK with ADB, open connection settings, enter your robot address and SSH credentials, CONNECT, then Open VR. The optional installer also installs the offline Cori voice engine after verifying its download checksum.

Build with `tools/build.ps1 -Target Quest`; output: `dist/TeleNao-Quest.apk`. CONNECT deploys the bundled bridge over SSH.

Some internal package/protocol names retain TelePepper names. User-facing branding and app identity are TeleNao. Pepper tablet, depth-camera and full-body animation features are unavailable on this NAO.

## Privacy

Repository and release packages exclude robot passwords, pairing tokens, personal network addresses, recordings and device captures. Passwords are stored on Quest using Android Keystore encryption; pairing information remains in private app storage. Setup checks SSH host keys. Never commit local settings, signing keys or diagnostic captures.

Run `python tools/privacy_check.py --apks` before publication. See [Security](SECURITY.md) and the third-party notices included in the source.

## Validation and licence

Experimental port: builds, regressions, audible voice confirmation and disarmed camera/network checks do not establish physical tracking accuracy or gait stability. See [Validation](docs/VALIDATION.md). V5/V6 support remains open until real-device testing.

Apache-2.0, retaining upstream and third-party notices. Robot firmware and SDK components retain their own licences.
