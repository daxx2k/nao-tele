# TeleNao validation history

Current release: 0.1.28-nao-test. Sections below record earlier configurations and tests, not necessarily current behavior. See README for current controls. NAO v4 H25 / NAOqi 2.1 has live validation; v5/v6 H25 are enabled, with physical validation pending.

## Explicit Exit and Autonomous Life (0.1.28)

Explicit Exit waits for STOP, requests Autonomous Life `solitary`, and verifies `solitary` or `interactive` before releasing the pilot and stopping the service. A newer STOP, timeout or failed state confirmation cancels the handoff and attempts to restore `disabled` and stop motion. Ordinary disconnect and local-only close do not enable autonomy. The Quest client also requires the reported life state, so an older bridge's generic success reply cannot confirm this handoff. This uses the native [NAOqi 2.1 API](https://fileadmin.cs.lth.se/robot/nao/doc/naoqi/core/autonomouslife-api.html) and [NAOqi 2.8 API](https://app.osrw.de/NAO/aldeb-doc-2.8.7.4/naoqi/interaction/autonomouslife-api.html).

Validation: all 118 Python tests passed, including 15 exit/protocol cases covering ordering, confirmation, timeout, interrupted handoff and rollback failures. The Quest APK built successfully and was installed as an update. Autonomous Life handoff was not triggered on hardware during this validation; V6 physical proof and the operator's Quest Exit interaction remain pending.

Derived from the nao branch, with separate Android identity and private settings.

- Quest APK built successfully with SDK 34, NDK 27.2 and OpenXR.
- Installed beside the existing TeleNao app on Quest 3.
- Private pairing configuration imported and SSH secret encrypted by Android Keystore.
- 49 active Python regression checks passed, including posture interlocks, walking gates,
  walking speed caps, deadman release, STOP completion, explicit re-arm, model/version checks and exit.
- NAO v4 H25 / NAOqi 2.1.4.13 confirmed live.
- Head service started disarmed; fresh telemetry received with no sensor/service errors.
- Both RGB cameras produced JPEG streams using the robot's legacy Pillow runtime.
- Quest reached the robot SSH service directly over Wi-Fi.
- Source/APK privacy scan performed; no embedded lab credentials.

Still requiring supervised physical verification: native preset transitions, actual gait and
turning, STOP response during physical walking, pose accuracy, headset tracking and end-to-end latency.
No posture or walking trial was triggered during deployment.

The inherited Robot-only motion/speech-gesture cases are retained under tests/nao_reference.
They describe incompatible Robot geometry and policies; active NAO coverage is tests/test_nao.py.

## Disconnection investigation

- Repeated control/video timeouts observed on Quest during a supervised user trial.
- Ethernet observer requests: median 7.3 ms, maximum 38.4 ms over 20 requests.
- Direct Quest Wi-Fi probe failed even without video; observed control delays up to 1.7 seconds.
- Reassociating robot Wi-Fi did not eliminate the timeouts.
- Corrected native discovery to the TeleNao protocol; its Android regression executable passed.
- Reduced requested video rates to 10/5 fps and paced latest pose datagrams to at most 50 Hz.
- Updated native posture speed from 0.25 to the standard example value 0.5.
- Revised APK installed; robot service restarted disarmed.
- Stable wireless teleoperation remains unverified; a robot Ethernet connection to the router
  is the next diagnostic step.

## Control-session fix

- An isolated one-byte echo server on the actual control port completed 100 Quest exchanges
  (median 9.4 ms; maximum 791 ms), separating radio jitter from bridge payload handling.
- Authentication still has a 3-second deadline. Authenticated control idle tolerance is now
  10 seconds; the local 180 ms motion watchdog and explicit re-arm policy are unchanged.
- Quest requests compact status without repeated history and unsupported tablet payloads.
  The observed response shrank from 4,164 to 1,494 bytes. Full observer diagnostics remain available.
- The revised control test completed 150 Quest requests without disconnecting
  (median 33.9 ms; maximum 1,802 ms). This proves session survival in that test,
  not acceptable physical teleoperation latency or long-term wireless stability.
- Revised APK installed on Quest; no motor commands or posture trial issued during this fix.

## Single-camera legacy video

- Simultaneous top/bottom streams reintroduced control/video stalls in the direct Quest probe.
- The app now selects one RGB camera at a time; Top and Bottom remain individually selectable.
- Robot capture uses QQVGA 160 x 120 JPEG at quality 35; video pull-credit idle tolerance is
  10 seconds and Quest video receive tolerance is 5 seconds. These are transport settings,
  not permission to continue motion with stale tracking or video.
- The final wireless probe completed 60 compact control requests and 83 top-camera frames
  without a socket error (median control latency 35.1 ms; maximum 2,559 ms).
- Large jitter is still present; low-latency physical teleoperation and posture completion
  must not be inferred from these disarmed session checks.
- Native camera exclusivity regression passed on Quest. Final APK installed; 49 Python checks pass.

## Feature parity / 0.1.1

- Native Sit executed at standard preset speed and robot posture confirmed Sit, disarmed.
- Posture buttons moved into the existing motion-animation grid.
- 58 Python checks pass, including native arm resource parsing, degree conversion, measured-pose start, bounds/speed limits, safe cancellation, and chest-channel routing.
- Native dashboard layout and exclusive camera selection checks passed on Quest.
- Quest natural-voice synthesis self-test passed three queued clips including a repeated preset.
- Direct Quest-to-robot live voice: 113 packets, no audio errors, disarmed.
- Direct Quest-to-robot clip voice: played=true. Operator confirmed the earlier audible phrase clearly.
- Robot microphone: 74 packets with nonzero signal.
- Eyes, ears, head and feet LED channels read back correctly. Chest RGB uses direct normalized native channels; protocol readback confirmed the requested color after refresh.
- Native speech clips are read from installed NAO resources; a dry run verified all ten controlled joints are arms and velocities are bounded. Gesture motion itself was not triggered.
- Deployment removes generated Python bytecode for updated modules to avoid stale code on the old runtime.
- See FEATURE-PARITY.md for coverage and remaining differences.

- Additional native checks passed on Quest: START flow, pose mirroring, speech grip chord and voice gain.
- The NAO kinematics check exposed a shoulder-branch jump for human lateral targets beyond NAO reach.
  A continuity term now prefers the anatomical seed/previous branch; both arms remain continuous around 90 degrees.
- Updated NAO geometry checks pass 216 FK/IK round trips, unequal human bone lengths, near-face goals, symmetry and unreachable-target bounds. These are model checks, not physical calibration proof.
# Posture failure investigation, 2026-10-09

Native NAOqi logs reported RKneePitch at 88 C with thermal status 1; live
readback later showed 73 C and status 1. PostureManager also reported
perturbations during goToPosture. This supports a motor protection problem,
but does not prove every earlier interruption had the same cause: pilot
disconnects can also cancel native preparation.

Quest TeleNao was force-stopped to suspend posture trials. Read-only SDK
verification reported Stand / Standing, all body stiffnesses 1, no active
ALMotion tasks. No new Stand or Sit trial was performed while the alarm was
active. The previous successful Sit does not establish current pose reliability.

Version 0.1.2 checks all physical joint thermal statuses before initiating a
native posture, fails closed on missing data, and reports hot joints. Native
speed remains 0.5; cancellation messages preserve the STOP/disconnect reason.
All 62 Python tests passed. The deployed guard was verified on NAOqi 2.1:
it rejected RKneePitch while status 1 was active without issuing a posture.
Physical completion still requires a trial after cooling.

The guard also covers START preparation and arming. Quest logs showed periods
with video available but body tracking false, and separate control reconnects.
No recorded START cancellation established which condition blocked the user's
attempt. START now logs button selection and individual prerequisites and shows
the missing prerequisite instead of the generic look-forward instruction.
The native start-flow tests, including all four waiting reasons, passed on Quest.
The revised APK was installed and opened; successful physical puppeteering has
not been verified.

## TeleNao 0.1.4 â€” standing-only control, Motion cleanup and latency (2026-10-10)

- START requires fresh standing telemetry on Quest and a native Standing family
  check on the robot. During telepresence, missing/non-standing/stale stance
  telemetry disarms control. It never initiates Stand automatically.
- Removed the two independent posture/walking cards; consolidated their data in
  Motion. Existing eleven-card layouts migrate to the nine surviving cards.
- Ported current TeleNao setup fixes: Home-based setup/VR transitions, compact
  scrollable form with a persistent entry button, and pairing storage per address.
  SSH bootstrap and credentials remain NAO-specific. Comparison found no newer
  C++ transport commits in the checked local TeleNao history.
- Active following submits the newest bounded reference directly, including hand
  aperture. Initial measured-pose blending remains three seconds. Native speed
  fractions: head 0.25, arms 0.5, hands 0.6; engagement remains 0.12/0.15. Robot
  joint limits, collision protection, thermal checks and watchdogs remain active.
- All 66 Python tests passed. Native START, floating layout and dashboard tests
  passed on Quest. Pairing recovery/isolation Java tests passed on Quest.
- Built and installed APK 0.1.4/code 5; updated robot bridge. Read-only status
  reported Stand, standing=true, motion_ready=true and walking_ready=true.
- Wi-Fi subsequently lost its address (saved Wi-Fi idle/connect-failed) independently
  of app sockets. After rescan/reconnect it obtained a Wi-Fi address again. A fresh
  Quest-to-NAO observer check completed 60 requests without errors: median 29.389
  ms, maximum 369.145 ms. This is control round-trip latency, not end-to-end
  physical motion latency. Sustained wireless stability and physical 1:1 following
  need live operator validation. No motor movement was initiated by these checks.

## TeleNao 0.1.5 (2026-10-10)

Automatic torso-heading rotation is disabled on both ends. Left stick XY drives
translation; right X rotates. Centred sticks never start moveToward; release uses
stopMove. Right Y controls native continuous torso height, initially limited to
4 cm downward and 2.5 cm/s, with a 26 cm torso-height floor. Centred Y holds
height. Height adjustment and walking are mutually exclusive; STOP captures and
holds measured legs. Physical height control remains unverified.

Camera receipt no longer gates body tracking or START. Live Quest-to-NAO test
completed 12 Top/Bottom/OFF switches and 120 snapshots with zero control-session
losses, zero stale UDP snapshots and zero unexpected arming. No motors moved.

Temporary command timeouts allow a five-second recovery window: fresh tracking
and centred sticks for 0.5 seconds, native STOP complete and verified standing.
Explicit STOP, tracking loss and pilot disconnect cancel recovery. Full TCP
reconnection stays disarmed. Recovery blends from measured pose over 0.5 seconds.
Saved Wi-Fi reconnect runs only while stopped, with one pending SDK request and
bounded retry frequency. Pairing probes now allow two seconds for replies.
The 180 ms robot input watchdog remains active.

Per user request, START and recovery have no application thermal veto. Warnings
remain visible and firmware protections remain active. Explicit posture preset
thermal checks remain unchanged. All 77 Python tests passed; native joystick
mapping tests passed on Quest. APK 0.1.5/code 6 and robot service were installed.

Cartesian API reference: [Aldebaran NAOqi 2.1 documentation](https://www.bx.psu.edu/~thanh/naoqi/naoqi/motion/control-cartesian-api.html).

## TeleNao 0.1.6 (2026-10-10)

Forward/backward input cap increased from 0.10 to 0.35. Lateral and rotation
caps remain 0.10. Runtime getMoveConfig readback confirmed default MaxStepX
0.04 m and maximum 0.08 m; the new moveToward configuration requests 0.06 m.
This is a maximum step setting, not a promise of six-centimetre steps at partial
stick input. Standing/height gates and joystick-release STOP remain active.
All 78 Python tests passed, including diagonal bounds and native gait config.
Built APK 0.1.6/code 7 and deployed the updated profile. Faster physical gait
still requires operator validation; no autonomous gait test was initiated.

## TeleNao 0.1.7 (2026-10-10)

Compared with upstream main (4efa691). Ported missing discovery changes:
interface broadcasts, repeated UDP requests and authenticated saved-endpoint TCP
fallback. Adapted discovery and saved-pairing tests passed on the host JVM. The
Android shell test process was killed twice; those tests are not claimed as
passing on Quest.

Fixed a NAO regression: height packets were ignored whenever torso_assist was
false. SDK command submissions now use a bounded worker off the tracking lock,
with a STOP generation barrier and a drain before measured-pose holds. Tests
exercise blocked SDK submission, cancellation of queued requests and height
delivery without torso assist. This changes software dispatch latency; physical
motion latency requires an operator test.

Top and Bottom can stream simultaneously at 5 fps each, with independent toggles.
Live 15-second Quest-to-NAO test: 61 Top frames and 55 Bottom frames, distinct
last images, zero connection breaks, zero stale UDP snapshots, zero unexpected
arming. Additional native image metadata verified camera source IDs 0 and 1,
both at 160x120, from concurrently registered subscriptions. All 81 Python tests
passed, as did native independent-camera selection.
APK 0.1.7/code 8 and robot service installed; both feed settings enabled.
Robot remained disarmed during automated network tests.

## TeleNao 0.1.8 (2026-10-10)

Adaptive camera rate: one RGB feed requests 30 fps, two feeds request 5 fps each.
Changing this mode restarts only the affected video subscriptions; the control
session and motion watchdog are independent. Resolution and JPEG quality are
unchanged. Backend accepts requests up to 30 fps.

Live single-camera tests with disarmed synthetic tracking: requesting 30 fps
delivered 148 frames in 10 seconds (14.8 fps); requesting 20 fps delivered 111
frames (11.1 fps). Both runs had zero control breaks and zero stale UDP samples.
Actual delivered rate is not the requested rate, and depends on robot/link load.
All 81 Python tests and native adaptive-rate/control-state tests passed.

Connection settings use two fixed columns with a persistent Open VR button. The installed Quest view was rendered and visually checked: all fields and actions fit, with no scroll container. Private SSH credentials use Android Keystore encryption and are excluded from published artifacts.

## TeleNao 0.1.9

Explicit START now prepares native StandInit at standard speed 0.5 when not standing or torso height is below 26 cm. Telemetry includes measured torso height in readiness, preventing calibration/ARM from skipping preparation. Already standing skips the preset. Cancellation/failure leaves control disarmed; automatic recovery never requests a stand-up. Added regressions cover crouch, low torso despite Standing family, already-standing bypass, failure and cancellation. Physical stand-up from START still requires an operator trial.

## TeleNao 0.1.10

All joystick axes now have a 50% normalized cap; translation diagonals share it. Right-stick dominant-axis selection prevents incidental vertical input from cancelling rotation. Motion adds a saved Smooth/Balanced/Quick response setting. Translation acceleration is vector-bounded (0.35/0.70/1.05 normalized units/s); rotation uses 0.40/0.80/1.20. Balanced is the default. STOP and centred-stick release use native stopMove without a software delay. Physical lateral movement, turning and the new response profiles remain unverified; no robot motion was initiated during development.

89 Python regressions passed; joystick, dashboard-layout and START native tests passed on Quest without connecting to NAO or requesting robot motion. The Quest APK built successfully. The response control fits within Motion without overlapping the native posture buttons. This release is not yet installed on the robot.

## TeleNao 0.1.11

Targets H25 v4-v6 / NAOqi 2.1-2.8, including VERSION_40/50/60 and replacement-head combinations. Live joint limits, required services and all motion interlocks remain checked. V4 has physical evidence; V5/V6 are enabled for supervised tests and are not claimed as physically validated.

Installer probes python2.7/python2/python/python3 commands for native qi/Pillow imports and local NAOqi service connectivity, preserving SDK environment variables. It preserves existing pairing, stops the app-owned legacy service only while disarmed, and installs the bundled bridge on each CONNECT.

Bridge files now live in nao/bridge, with telenao.py, manage.py and runner.py. Java packages and the native library use it.telenao/telenao. Application ID, preferences and Keystore alias remain unchanged. Removed obsolete packages, incompatible archived tests and unused artwork/tools; origin attribution remains in legal notices.

94 Python regressions and host Java runtime-selection tests passed. The Quest APK built successfully. No NAO deployment or motion was requested during development. V5/V6 camera, speech, posture and gait operation still require physical verification.

Updated the existing Quest installation in place: saved connection and encrypted credential files were byte-identical before and after installation. The renamed it.telenao.quest.LauncherActivity opened successfully without robot connection. APK scan found no legacy branding, and confirmed libtelenao.so and the assets/nao/telenao.py bridge.

## TeleNao 0.1.12

An operator reported posture buttons appeared to do nothing. Robot logs recorded repeated application thermal refusals for hip/knee/ankle joints; after reboot the currently queried affected sensors reported normal status. Motion now shows posture preparation, cancellation and failure messages, with an explicit thermal-block summary and a STOP-first refusal. Control logs also include refused posture commands. Native posture dispatch and thermal checks are unchanged. No automated posture movement was requested in this investigation.

Thermal refusal diagnostics now include the native status per affected joint rather than labelling every nonzero state generically as too hot. Per Aldebaran, temperature is a current-based estimate; status 1 begins stiffness reduction, status 2 denotes stronger reduction and status 3 disables motor stiffness. There is no guessed Celsius threshold or override of native protection.

## TeleNao 0.1.13

Removed the application-level posture temperature veto at the operator request. START, recovery and presets do not reject requests based on temperature readings or status. Temperature telemetry stays visible; native NAOqi torque reduction, motor shutdown and posture failure responses remain intact. Tests verify that presets dispatch with reported thermal statuses 1/2/3 or unavailable telemetry, while native failure and cancellation still leave control disarmed. No firmware protection setting was changed.

## 0.1.23-nao-test: arm mapping (2026-10-16)

- Ported the TelePepper 0.3.19 shoulder-elevation correction using NAO geometry: 105 mm upper arm, 15 mm lateral elbow offset and 55.95 mm forearm.
- Replaced application-added shoulder, elbow and wrist position envelopes with live ALMotion.getLimits bounds. Published H25 values are the compatibility fallback; mirrored mapping reflects the destination arm bounds.
- Kept NAO solver regularization for unreachable human poses and a level seed near the horizontal lateral singularity. Candidate selection no longer retains a less accurate previous pose merely through its old error allowance.
- 107 Python regression checks pass, including native bound propagation, status export, posture gates, walking and STOP.
- C++ tests pass on Windows and Quest: 1,200 overhead/native-envelope cases, 216 forward/inverse round trips, moving overhead targets with production continuity selection, asymmetric live bounds and mirror reflection, malformed-profile fallback, face reach, horizontal continuity and unreachable goals. Native shoulder roll cannot fully reproduce a human T-pose; tests measure the constrained residual (less than 0.08 rad wrist elevation) instead of expanding hardware bounds.
- Updated stale native-test rotation expectations to match the existing 50% walking/rotation cap; production locomotion settings were not changed.
- Speeds, gradual engagement, head policy, native collision safeguards, walking/height controls and STOP remain unchanged.
- No NAO motion was initiated. Physical NAO tracking accuracy and latency remain unverified for this build. Pepper operator feedback does not substitute for that trial.
