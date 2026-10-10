# TeleNao / TelePepper feature audit

TeleNao 0.1.8 derives from the TelePepper `pepper25` branch. Shared Quest control and media paths were compared with that branch; Android-tablet features on the main branch were also checked for relevance.

| Feature | TeleNao result | Verification |
|---|---|---|
| Quest head, arms, wrists, trigger hands | Same controls, NAO lengths and hardware limits | Code review, native build, joint-limit tests, 216 native FK/IK round trips and T-pose continuity checks; physical pose accuracy still needs operator trials |
| START, calibration, mirror, STOP, watchdog | Preserved; guarded brief-timeout recovery; explicit START after full reconnection | Regression checks; Sit executed and confirmed live |
| Joystick movement / height | Native NAO walking with standing/awake gates and 35% forward/back cap, 10% sideways/turn, bounded continuous height | Input/gating tests; physical gait is still unvalidated |
| Manual animation panel | StandInit, Stand, Sit, Crouch in the original motion-animation grid | Native layout checks and live Sit |
| Automatic speech gestures | Native NAO conversation resources, arms only; OFF by default | Three installed clips parsed; dry-run scheduling verifies only ten arm joints, measured-pose start, hardware bounds and speed caps; no physical gesture run yet |
| Live puppeteer voice | Preserved | 113 PCM packets sent from Quest to robot with no audio error; separate audible phrase confirmed by the operator |
| Piper/Cori clip voice | Preserved | Quest local synthesis queue self-test passes three clips; Quest-to-robot clip acknowledged playback |
| Robot TTS / phrase presets | Preserved; English and Italian installed | Services/languages confirmed live; shared allowlisted phrase path inspected |
| Robot microphone / Listen | Preserved | 74 microphone packets received with nonzero signal |
| Volume and Stop speech | Preserved | Volume readback 65%; output and cancellation paths reviewed |
| Eyes / ears / chest LEDs | Eyes RGB; ears intensity of fixed blue LEDs; chest RGB via verified individual channels | Live channel readback; chest packed-color issue fixed |
| NAO-specific head / feet LEDs | Added: head intensity, feet RGB | Live channel readback and native layout checks |
| Camera controls | Both RGB cameras together at 5 requested fps each; single feed requests 30 fps | Native camera-selection test; disarmed wireless frame test |
| Battery, temperatures, touches, sonar, bumpers | NAO telemetry mappings; missing sensors remain null | Live sensor API and key discovery; foot-bumper mappings corrected |
| Floating panels, layout save/load, Help, connection/pairing | Shared behavior retained; NAO wording and layouts updated | Native dashboard/layout and discovery tests |
| Tablet display, depth camera, Pepper lidar | No corresponding hardware on this NAO | Hidden/excluded from Quest controls |
| Pepper torso, full-body Pepper animations | Excluded; native NAO posture/gait own the legs | No arbitrary behavior dispatch or Pepper hip/wheel calls |
| Speed/range disable switches, automatic fault re-arm | Hardware bounds retained; guarded recovery of previously armed sessions | Safeguards remain enabled; this is a deliberate port policy, not an asserted hardware limitation |

Coverage is not a claim that every feature was physically tested. This audit includes code comparison, mock regressions, native checks on Quest and the specific live tests listed above. Wireless jitter remains significant; session survival does not prove physical low latency.
