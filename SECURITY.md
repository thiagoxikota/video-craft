# Security

The included scripts process local media with Python and FFmpeg. They do not download assets, call APIs, collect telemetry or publish output. FFmpeg and Python updates remain the user's responsibility; do not treat untrusted media parsing as a sandbox.

Commands are passed as subprocess argument arrays without a shell. Inputs accept local files only, with FFmpeg/ffprobe protocols restricted to file and pipe. Local playlists may still reference other local files; run unknown inputs in an isolated environment with only the intended files mounted. A file path is not a rights or trust assertion.

No secrets or private source media belong in this repository. The installer copies only the skill directory and refuses an existing destination. Output replacement requires `--force`; source clips cannot be selected as the assembly destination. Public videos may still expose private content visible in their pixels or audible in their sound.

Report a reproducible security issue through GitHub's private vulnerability reporting feature when available, or open an issue without credentials, exploit payloads or personal data and request a private contact. Do not attach client media. No security audit or sandbox guarantee is claimed.
