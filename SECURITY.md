# Security and private configuration

TeleNao is an experimental local-network robot-control app. Use a trusted network, keep robot control ports off the public Internet, and retain physical access to the robot's stop controls.

CONNECT uses owner SSH credentials, checks the SSH host key and deploys the bridge manually. Quest stores passwords encrypted through Android Keystore and stores pairing tokens in private application data; Android backup is disabled. Credentials are not included in releases.

Do not attach passwords, tokens, network names, personal addresses, raw device logs or recordings to public issues. Report reproducible problems with redacted details. Use GitHub's private vulnerability reporting when available for security issues; never publish an exploit involving live robots or exposed credentials.

Before publishing, run `python tools/privacy_check.py --apks` and inspect the release packages. Keep `.local`, local settings, captures and signing keys out of version control. A successful privacy scan is an additional check, not a guarantee that arbitrary new files are safe to publish.
