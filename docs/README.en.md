# Video Craft

A portable agent skill for turning local footage into intentional edits, with sound craft and checks on the exported file. Includes editorial guidance and a dependency-free Python CLI powered by FFmpeg.

## Install in Claude Code

```text
/plugin marketplace add thiagoxikota/video-craft
/plugin install video-craft@video-craft-tools
```

Invoke `/video-craft:video-craft` with your brief and local footage paths. This is an independent community plugin, not an Anthropic product. No hooks, MCP servers or background processes are installed.

Alternatively, clone the repository and copy the skill to a project:

```bash
git clone https://github.com/thiagoxikota/video-craft.git
cd video-craft
python3 install.py --target claude --project /path/to/project
```

Use `--target codex` for Codex, `--scope user` for a personal installation, or `--dry-run` to inspect the destination. Existing skills are never overwritten. The release ZIP can be uploaded to a compatible Claude Skills environment; FFmpeg availability and execution permissions must be checked separately. Local rendering was tested; cloud execution is not guaranteed.

## Render locally

Requires Python 3.10+, FFmpeg with libx264/AAC, and ffprobe. No Python packages or credentials required. Install FFmpeg using your platform's trusted package manager or the builds linked from [ffmpeg.org](https://ffmpeg.org/download.html).

```bash
python3 skills/video-craft/scripts/video_craft.py doctor
python3 skills/video-craft/scripts/video_craft.py demo out/test.mp4
python3 skills/video-craft/scripts/video_craft.py sheet out/test.mp4 out/contact.jpg
python3 skills/video-craft/scripts/video_craft.py verify out/test.mp4 --require-audio --peak -2
```

The four-second demo is a synthetic technical fixture, not a finished editorial showcase. For actual footage, copy the [timeline template](../skills/video-craft/assets/timeline.json), replace the paths/timing, then run `assemble timeline.json out/cut.mp4`.

The CLI handles cuts, trim, contain/cover reframing, keep/mute audio, loudness mastering and verification. It does not generate AI footage, layer graphics, add captions or mix music automatically. The skill guides those editorial decisions and optional Remotion composition separately.

`master` uses two-pass loudness processing and checks the final decoded AAC. Defaults are -14 LUFS and -2 dBTP, configurable for the brief. Silent, missing or excessively quiet audio is rejected. Sparse no-music edits should preserve their intentional silence instead of being full-program normalized.

## Verify and review

```bash
python3 -m unittest discover -s tests -v
```

Technical checks do not prove narrative quality, licensing, accessibility or synchronization. Watch and listen to the complete export, inspect frames, and keep asset provenance. No network calls, telemetry, credentials or uploads are required by the included scripts. Originals and existing outputs are preserved by default.

[MIT license](../LICENSE). Created by Thiago Xikota. Independent project, not affiliated with Anthropic, FFmpeg or Remotion. See the [Portuguese README](../README.md) for detailed usage, limitations and contribution links.
