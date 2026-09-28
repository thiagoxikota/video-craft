#!/usr/bin/env python3
"""Local, dependency-free orchestration for FFmpeg. Python 3.10+."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

VERSION = "1.0.0"


class CraftError(Exception):
    pass


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.returncode:
        raise CraftError(f"{Path(str(args[0])).name} failed ({result.returncode}):\n{result.stderr[-2500:]}")
    return result


def tool(name):
    binary = os.environ.get(name.upper(), name)
    found = shutil.which(binary)
    if not found:
        raise CraftError(f"Missing {name}. Install FFmpeg or set {name.upper()} to its executable.")
    return found


def ff(*args):
    return run([tool("ffmpeg"), "-hide_banner", "-nostdin", "-y", "-protocol_whitelist", "file,pipe", *args])


def local_file(value):
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", str(value)):
        raise CraftError("Only local files are accepted. Download explicitly before processing.")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise CraftError(f"File not found: {path}")
    return path


def probe(value):
    path = local_file(value)
    data = json.loads(run([tool("ffprobe"), "-v", "error", "-protocol_whitelist", "file,pipe", "-show_format", "-show_streams", "-of", "json", path]).stdout)
    data["path"] = str(path)
    return data


def stream(data, kind):
    return next((s for s in data["streams"] if s["codec_type"] == kind), None)


def duration(data):
    try:
        value = float(data["format"]["duration"])
    except (KeyError, ValueError):
        raise CraftError("File has no readable duration.")
    if not math.isfinite(value) or value <= 0:
        raise CraftError("Invalid duration.")
    return value


def number(value, label, lower=0, upper=86400):
    if isinstance(value, bool):
        raise CraftError(f"{label} must be a number.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise CraftError(f"{label} must be a number.")
    if not math.isfinite(value) or not lower <= value <= upper:
        raise CraftError(f"{label} must be between {lower} and {upper}.")
    return value


def output_path(value, force=False):
    path = Path(value).expanduser().absolute()
    if path.exists() and not force:
        raise CraftError(f"Output exists: {path}. Choose a new path or use --force.")
    if path.is_symlink():
        raise CraftError("Refusing a symlink output.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def publish(tmp, dest, force):
    # Link is an atomic, no-clobber publication on the same filesystem.
    if force:
        os.replace(tmp, dest)
    else:
        try:
            os.link(tmp, dest)
        except FileExistsError:
            raise CraftError(f"Output appeared during render: {dest}. Nothing was replaced.")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def measure_audio(path, target=-14, peak=-2):
    data = probe(path)
    if not stream(data, "audio"):
        return {"present": False}
    result = ff("-i", local_file(path), "-map", "0:a:0", "-af", f"loudnorm=I={target}:TP={peak}:LRA=11:print_format=json", "-f", "null", "-")
    chunks = re.findall(r'\{\s*"input_i".*?\}', result.stderr, flags=re.S)
    if not chunks:
        raise CraftError("FFmpeg did not return loudness measurements.")
    raw = json.loads(chunks[-1])
    def finite(key):
        value = float(raw[key])
        return value if math.isfinite(value) else None
    return {"present": True, "integrated_lufs": finite("input_i"), "true_peak_dbtp": finite("input_tp"),
            "loudness_range_lu": finite("input_lra"), "threshold_lufs": finite("input_thresh"), "raw": raw}


def inspect(path, audio=False):
    data = probe(path)
    v = stream(data, "video")
    result = {"file": Path(path).name, "duration_seconds": duration(data), "bytes": Path(path).stat().st_size,
              "video": None, "audio_streams": sum(s["codec_type"] == "audio" for s in data["streams"])}
    if v:
        result["video"] = {k: v.get(k) for k in ["codec_name", "width", "height", "pix_fmt", "avg_frame_rate", "color_space", "color_transfer", "color_primaries"]}
        result["video"]["rotation_degrees"] = next((x["rotation"] for x in v.get("side_data_list", []) if "rotation" in x), 0)
    if audio:
        result["audio"] = measure_audio(path)
    return result


def doctor():
    ffmpeg, ffprobe = tool("ffmpeg"), tool("ffprobe")
    filters = run([ffmpeg, "-hide_banner", "-filters"]).stdout
    encoders = run([ffmpeg, "-hide_banner", "-encoders"]).stdout
    return {"version": VERSION, "python": sys.version.split()[0], "ffmpeg": ffmpeg, "ffprobe": ffprobe,
            "ffmpeg_version": run([ffmpeg, "-version"]).stdout.splitlines()[0],
            "capabilities": {x: bool(re.search(r"\b" + x + r"\b", filters)) for x in ["loudnorm", "ebur128", "subtitles", "drawtext", "zscale"]},
            "encoders": {x: bool(re.search(r"\b" + x + r"\b", encoders)) for x in ["libx264", "aac"]}}


def sheet(args):
    src = local_file(args.input)
    data = probe(src)
    if not stream(data, "video"):
        raise CraftError("Contact sheets need a video stream.")
    count = int(number(args.count, "count", 1, 36))
    dest = output_path(args.output, args.force)
    if src == dest.resolve():
        raise CraftError("Contact sheet must not replace the source.")
    step = duration(data) / count
    cols = min(count, 4)
    rows = math.ceil(count / cols)
    with tempfile.TemporaryDirectory(prefix=".video-craft-", dir=dest.parent) as tmp:
        image = Path(tmp) / "sheet.jpg"
        ff("-i", src, "-vf", f"fps=1/{step}:start_time=0,scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2,tile={cols}x{rows}:nb_frames={count}", "-frames:v", "1", image)
        if not image.is_file() or image.stat().st_size < 100:
            raise CraftError("No contact sheet was produced.")
        publish(image, dest, args.force)
    return {"output": str(dest), "sampling_seconds": step, "requested_frames": count, "note": "Open the image to review framing, exposure and subject continuity."}


def validate_timeline(path):
    manifest = local_file(path)
    spec = json.loads(manifest.read_text())
    if not isinstance(spec, dict) or type(spec.get("version")) is not int or spec.get("version") != 1:
        raise CraftError("Timeline version must be 1.")
    allowed = {"version", "width", "height", "fps", "fit", "clips", "note"}
    if set(spec) - allowed:
        raise CraftError(f"Unknown timeline fields: {sorted(set(spec) - allowed)}")
    for key, default in [("width", 1080), ("height", 1920)]:
        val = number(spec.get(key, default), key, 64, 4096)
        if val % 2:
            raise CraftError(f"{key} must be an even integer.")
        spec[key] = int(val)
    fps = number(spec.get("fps", 30), "fps", 1, 60)
    spec["fps"] = fps
    if spec.get("fit", "contain") not in ["contain", "cover"]:
        raise CraftError("fit must be contain or cover.")
    spec["fit"] = spec.get("fit", "contain")
    clips = spec.get("clips")
    if not isinstance(clips, list) or not 1 <= len(clips) <= 100:
        raise CraftError("Provide 1 to 100 clips.")
    normalized = []
    for i, clip in enumerate(clips):
        if not isinstance(clip, dict) or set(clip) - {"file", "start", "duration", "audio", "note"}:
            raise CraftError(f"Invalid fields in clip {i + 1}.")
        value = clip.get("file", "")
        if not isinstance(value, str) or "://" in value:
            raise CraftError("Clip file must be a local path.")
        src = local_file(manifest.parent / value)
        data = probe(src)
        v = stream(data, "video")
        if not v:
            raise CraftError(f"Clip {i + 1} has no video.")
        if v.get("color_transfer") in ["smpte2084", "arib-std-b67"]:
            raise CraftError("HDR input needs deliberate tone mapping before assembly. See references/technical.md.")
        start = number(clip.get("start", 0), "start")
        length = number(clip.get("duration"), "duration", 1 / fps, 3600)
        if start + length > duration(data) + 0.02:
            raise CraftError(f"Clip {i + 1} extends past the input duration.")
        audio_mode = clip.get("audio", "keep")
        if audio_mode not in ["keep", "mute"]:
            raise CraftError("Clip audio must be keep or mute.")
        normalized.append({"file": src, "start": start, "duration": length, "audio": audio_mode == "keep" and bool(stream(data, "audio"))})
    spec["clips"] = normalized
    return spec


def assemble(args):
    spec = validate_timeline(args.timeline)
    dest = output_path(args.output, args.force)
    if dest.suffix.lower() != ".mp4":
        raise CraftError("Assembly output must end in .mp4.")
    if any(c["file"] == dest.resolve() for c in spec["clips"]):
        raise CraftError("Output must not replace a source clip.")
    w, h, fps = spec["width"], spec["height"], spec["fps"]
    scaler = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2" if spec["fit"] == "contain" else f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}")
    with tempfile.TemporaryDirectory(prefix=".video-craft-", dir=dest.parent) as tmp:
        folder = Path(tmp)
        for i, clip in enumerate(spec["clips"]):
            length = clip["duration"]
            inputs = ["-ss", clip["start"], "-i", clip["file"]]
            if clip["audio"]:
                amap = "0:a:0"
            else:
                inputs += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                amap = "1:a:0"
            ff(*inputs, "-map", "0:v:0", "-map", amap, "-t", length,
               "-vf", f"{scaler},setsar=1,fps={fps},format=yuv420p", "-af", "apad,aresample=48000",
               "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "pcm_s16le", "-ac", "2",
               "-map_metadata", "-1", "-map_chapters", "-1", folder / f"part-{i:03}.mkv")
        concat = folder / "concat.txt"
        concat.write_text("".join(f"file 'part-{i:03}.mkv'\n" for i in range(len(spec["clips"]))))
        result = folder / "result.mp4"
        ff("-f", "concat", "-safe", "1", "-i", concat, "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1", "-map_chapters", "-1", "-movflags", "+faststart", result)
        check = probe(result)
        expected = sum(c["duration"] for c in spec["clips"])
        if abs(duration(check) - expected) > max(0.2, len(spec["clips"]) / fps):
            raise CraftError("Rendered duration differs from timeline. Output was not published.")
        publish(result, dest, args.force)
    return {"output": str(dest), "sha256": sha256(dest), "duration_seconds": duration(check), "clips": len(spec["clips"]), "audio": "Preserved or silent placeholder; not loudness-mastered.", "status": "rendered; visual and listening review required"}


def master(args):
    src = local_file(args.input)
    dest = output_path(args.output, args.force)
    if src == dest.resolve() or dest.suffix.lower() != ".mp4":
        raise CraftError("Use a new .mp4 output path.")
    if not stream(probe(src), "video"):
        raise CraftError("Mastering expects a video file.")
    target = number(args.lufs, "lufs", -30, -10)
    peak = number(args.peak, "peak", -9, -1)
    measured = measure_audio(src, target, peak)
    if not measured["present"] or measured["integrated_lufs"] is None:
        raise CraftError("Missing or silent audio; loudness normalization is not appropriate.")
    if target - measured["integrated_lufs"] > 12:
        raise CraftError("More than 12 dB gain required. Review noise and sparse audio instead of boosting blindly.")
    raw = measured["raw"]
    chain = (f"loudnorm=I={target}:TP={peak}:LRA=11:measured_I={raw['input_i']}:measured_TP={raw['input_tp']}:"
             f"measured_LRA={raw['input_lra']}:measured_thresh={raw['input_thresh']}:offset={raw['target_offset']}:linear=true:print_format=json")
    with tempfile.TemporaryDirectory(prefix=".video-craft-", dir=dest.parent) as tmp:
        out = Path(tmp) / "master.mp4"
        ff("-i", src, "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-af", chain, "-ar", "48000", "-c:a", "aac", "-b:a", "256k", "-map_metadata", "-1", "-map_chapters", "-1", "-movflags", "+faststart", out)
        after = measure_audio(out)
        if after["integrated_lufs"] is None or abs(after["integrated_lufs"] - target) > 0.6 or after["true_peak_dbtp"] > peak:
            raise CraftError(f"Decoded AAC missed targets (I={after['integrated_lufs']}, TP={after['true_peak_dbtp']}). No final file published. Adjust the mix, then retry.")
        publish(out, dest, args.force)
    return {"output": str(dest), "sha256": sha256(dest), "measured_decoded_aac": after, "note": "Technical measurement, not a substitute for listening."}


def verify(args):
    if args.lufs is not None:
        args.lufs = number(args.lufs, "lufs", -70, 0)
    if args.peak is not None:
        args.peak = number(args.peak, "peak", -90, 0)
    result = inspect(args.input, audio=True)
    issues = []
    if not result["video"]:
        issues.append("No video stream.")
    elif result["video"]["pix_fmt"] != "yuv420p":
        issues.append("Pixel format is not yuv420p; check playback compatibility.")
    a = result["audio"]
    if args.require_audio and (not a["present"] or a.get("integrated_lufs") is None):
        issues.append("Required audible audio is missing.")
    if args.peak is not None and a["present"] and a["true_peak_dbtp"] is not None and a["true_peak_dbtp"] > args.peak:
        issues.append(f"True peak exceeds {args.peak} dBTP.")
    if args.lufs is not None:
        if not a["present"] or a["integrated_lufs"] is None or abs(a["integrated_lufs"] - args.lufs) > 0.6:
            issues.append(f"Integrated loudness is not within 0.6 LU of {args.lufs} LUFS.")
    result.update({"sha256": sha256(local_file(args.input)), "issues": issues, "technical_pass": not issues, "editorial_review": "Still required: watch, listen, check captions and rights."})
    return result


def demo(args):
    dest = output_path(args.output, args.force)
    if dest.suffix.lower() != ".mp4":
        raise CraftError("Demo output must end in .mp4.")
    with tempfile.TemporaryDirectory(prefix=".video-craft-", dir=dest.parent) as tmp:
        out = Path(tmp) / "demo.mp4"
        ff("-f", "lavfi", "-i", "testsrc2=size=360x640:rate=30:duration=4", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=4", "-vf", "format=yuv420p", "-af", "volume=0.4,afade=t=in:d=0.2,afade=t=out:st=3.8:d=0.2", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-map_metadata", "-1", "-map_chapters", "-1", "-movflags", "+faststart", out)
        probe(out)
        publish(out, dest, args.force)
    return {"output": str(dest), "purpose": "Synthetic technical fixture, not an example of editorial craft.", "sha256": sha256(dest)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Discover actual FFmpeg capabilities")
    p = sub.add_parser("inspect", help="Inspect a local media file")
    p.add_argument("input"); p.add_argument("--audio", action="store_true")
    for name in ["sheet", "master"]:
        p = sub.add_parser(name)
        p.add_argument("input"); p.add_argument("output"); p.add_argument("--force", action="store_true")
        if name == "sheet": p.add_argument("--count", type=int, default=12)
        else:
            p.add_argument("--lufs", type=float, default=-14); p.add_argument("--peak", type=float, default=-2)
    p = sub.add_parser("assemble", help="Render a local JSON timeline")
    p.add_argument("timeline"); p.add_argument("output"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("verify")
    p.add_argument("input"); p.add_argument("--require-audio", action="store_true")
    p.add_argument("--lufs", type=float); p.add_argument("--peak", type=float)
    p = sub.add_parser("demo")
    p.add_argument("output"); p.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "doctor": result = doctor()
        elif args.command == "inspect": result = inspect(args.input, args.audio)
        else: result = globals()[args.command](args)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 2 if result.get("technical_pass") is False else 0
    except (CraftError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"video-craft: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
