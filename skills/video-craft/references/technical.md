# Rendering and verification

## Environment first

Run `doctor`: FFmpeg builds differ. `subtitles`, `drawtext`, `zscale` or particular encoders may be missing. Do not infer availability from the operating system or a version someone reported. Set `FFMPEG` and `FFPROBE` to explicit executable paths when using a separate build. These are executable overrides, never shell fragments.

The bundled CLI needs Python 3.10+, FFmpeg with libx264/AAC and ffprobe. It executes local programs with argument arrays, without a shell. No runtime network calls, telemetry, API keys, daemons or hooks. Review software from any source before installing it.

## Timeline contract

The version-1 JSON timeline accepts width/height (even, 64–4096), fps (1–60), fit (`contain` or `cover`) and 1–100 clips. Each clip has a local `file`, `start`, `duration` and audio `keep`/`mute`. Paths are relative to the timeline file; absolute paths work too. The CLI rejects unknown fields, invalid numbers, missing video, intervals past the source, and HDR flagged as PQ/HLG.

`contain` preserves the full frame with padding. `cover` crops centrally. FFmpeg applies input rotation automatically; review the resulting frame rather than swapping width/height twice. Mixed inputs are normalized to a common frame rate, geometry, square pixels, H.264/yuv420p and stereo 48 kHz. Silent clips receive a silent placeholder track for concatenation. Metadata is stripped from generated videos, but visible private content is not detected or redacted.

Assembly supports straight cuts. It does not add music, burn captions, compose graphics, make transitions or isolate voices. Use an appropriate composition tool for those steps. The intermediate audio is PCM so each source is not AAC-encoded twice during assembly. Files are rendered in an isolated temporary directory and published only after validation. Existing files are protected unless `--force` was explicitly passed; original source clips cannot be chosen as the final assembly path.

## HDR and color

PQ/HLG footage requires a deliberate color workflow. Do not simply tag it BT.709: that changes metadata, not pixel values. Choose a tone-map operator, white level and output transfer appropriate to the material, and compare the result on the target display. If the installed build lacks the relevant filters, use a suitable build or preserve HDR through a compatible pipeline. The CLI refuses flagged HDR assembly to avoid silently washing out footage.

## Captions and richer motion

For captions, review a transcript grounded in the actual audio. Keep an editable SRT/VTT. FFmpeg burn-in requires its subtitles/libass support and usable fonts. Filenames inside filter syntax need separate filter-level escaping, even when the subprocess itself is shell-safe. For complex paths, stage a copy under a simple local filename before building the filter.

Use Remotion when React-based layers, diagrams and typography materially help. Create dependencies in the project, pin versions and consult [Remotion's official documentation](https://www.remotion.dev/docs/) and [official skills repository](https://github.com/remotion-dev/skills). Follow its current licensing terms for the intended usage. No Remotion runtime or skills are copied into this package. Do not install a framework globally just to render a single project.

Keep font and asset loading inside the composition lifecycle, await them before rendering, and avoid module-scope side effects that stall rendering. Make transitions overlap correctly. Test a short representative composition before spending resources on the full film. Do not assume a universal AAC delay offset; measure known audio/video events in the actual export.

## Verification and evidence

`inspect --audio` reports actual duration/streams/color metadata and decoded loudness. `verify --require-audio --lufs -14 --peak -2` returns a nonzero exit if a requested technical check fails. Omit loudness requirements for an intentionally sparse/silent version. Save output JSON next to the export. Include commands, tool version and the file hash so measurements remain tied to the right artifact.

This tool does not certify source rights, flash safety, semantic accuracy, transcription accuracy, lip sync or editorial quality. Open frames, watch the export and listen. `sheet` samples uniformly; short flashes and transient errors can occur between samples. No claim of a human listening review should be made unless one actually happened.

Official references, checked 2026-09-28:
- [FFmpeg filters, including loudnorm and ebur128](https://ffmpeg.org/ffmpeg-filters.html)
- [FFmpeg command-line documentation](https://ffmpeg.org/ffmpeg.html)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
