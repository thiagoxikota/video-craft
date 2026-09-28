"""End-to-end checks generate their own media and use no network."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'skills/video-craft/scripts/video_craft.py'
spec = importlib.util.spec_from_file_location('video_craft', CLI)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class VideoCraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.p = Path(cls.tmp.name)
        cls.media = cls.p / "fixture ' with spaces.mp4"
        v.demo(argparse.Namespace(output=cls.media, force=False))
        cls.silent = cls.p / 'silent.mp4'
        v.ff('-i', cls.media, '-an', '-c:v', 'copy', cls.silent)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def timeline(self, name, **change):
        d = dict(version=1, width=180, height=320, fps=30, clips=[dict(file=str(self.media), start=0, duration=1, audio='keep')])
        d.update(change)
        path = self.p / name
        path.write_text(json.dumps(d))
        return path

    def test_doctor_finds_actual_tools(self):
        self.assertTrue(v.doctor()['encoders']['libx264'])

    def test_inspect_real_streams(self):
        info = v.inspect(self.media, True)
        self.assertEqual(info['video']['width'], 360)
        self.assertAlmostEqual(info['duration_seconds'], 4, delta=.1)
        self.assertTrue(info['audio']['present'])

    def test_render_mixed_silent_audio_clips(self):
        timeline = self.timeline('mixed.json', clips=[dict(file=str(self.media), start=.2, duration=1), dict(file=str(self.silent), start=.1, duration=1)])
        out = self.p / 'mixed.mp4'
        v.assemble(argparse.Namespace(timeline=timeline, output=out, force=False))
        info = v.inspect(out, True)
        self.assertAlmostEqual(info['duration_seconds'], 2, delta=.1)
        self.assertEqual(info['video']['width'], 180)
        self.assertEqual(info['audio_streams'], 1)

    def test_contact_sheet_is_actual_image(self):
        out = self.p / 'sheet.jpg'
        v.sheet(argparse.Namespace(input=self.media, output=out, count=8, force=False))
        self.assertTrue(out.read_bytes().startswith(b'\xff\xd8'))

    def test_invalid_ranges_rejected_before_render(self):
        for length in [0, -2, 100, float('nan'), float('inf'), True]:
            path = self.timeline('bad.json', clips=[dict(file=str(self.media), duration=length)])
            with self.assertRaises(v.CraftError): v.validate_timeline(path)

    def test_unknown_fields_not_silently_ignored(self):
        with self.assertRaises(v.CraftError): v.validate_timeline(self.timeline('unknown.json', crossfade=1))

    def test_existing_output_protected(self):
        out = self.p / 'important.mp4'
        out.write_bytes(b'keep me')
        with self.assertRaises(v.CraftError): v.demo(argparse.Namespace(output=out, force=False))
        self.assertEqual(out.read_bytes(), b'keep me')

    def test_missing_audio_does_not_pass_required_audio(self):
        args = argparse.Namespace(input=self.silent, require_audio=True, lufs=None, peak=-2)
        self.assertFalse(v.verify(args)['technical_pass'])

    def test_master_refuses_missing_audio_without_final_file(self):
        out = self.p / 'never-created.mp4'
        with self.assertRaises(v.CraftError): v.master(argparse.Namespace(input=self.silent, output=out, force=False, lufs=-14, peak=-2))
        self.assertFalse(out.exists())

    def test_master_validates_encoded_output(self):
        out = self.p / 'master.mp4'
        result = v.master(argparse.Namespace(input=self.media, output=out, force=False, lufs=-20, peak=-2))
        self.assertAlmostEqual(result['measured_decoded_aac']['integrated_lufs'], -20, delta=.6)
        self.assertLessEqual(result['measured_decoded_aac']['true_peak_dbtp'], -2)

    def test_invalid_number_and_url_rejected(self):
        with self.assertRaises(v.CraftError): v.number(float('nan'), 'x')
        with self.assertRaises(v.CraftError): v.local_file('https://example.com/video.mp4')
        with self.assertRaises(v.CraftError): v.validate_timeline(self.timeline('url.json', clips=[dict(file='https://example.com/video.mp4', duration=1)]))

    def test_subprocess_does_not_evaluate_filename(self):
        path = self.p / '$(touch hacked).mp4'
        path.write_bytes(self.media.read_bytes())
        self.assertEqual(v.inspect(path)['video']['width'], 360)
        self.assertFalse((self.p / 'hacked').exists())

    def test_install_project_copy_and_protect_existing(self):
        target = self.p / 'clean-project'
        result = subprocess.run([sys.executable, ROOT / 'install.py', '--project', target], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        installed = target / '.claude/skills/video-craft'
        self.assertTrue((installed / 'SKILL.md').is_file())
        doc = subprocess.run([sys.executable, installed / 'scripts/video_craft.py', 'doctor'], capture_output=True)
        self.assertEqual(doc.returncode, 0, doc.stderr)
        second = subprocess.run([sys.executable, ROOT / 'install.py', '--project', target], capture_output=True)
        self.assertNotEqual(second.returncode, 0)

    def test_force_cannot_replace_input(self):
        path = self.timeline('self.json')
        with self.assertRaises(v.CraftError): v.assemble(argparse.Namespace(timeline=path, output=self.media, force=True))

    def test_contact_sheet_cannot_replace_source(self):
        with self.assertRaises(v.CraftError):
            v.sheet(argparse.Namespace(input=self.media, output=self.media, count=4, force=True))

    def test_nonfinite_verification_target_rejected(self):
        with self.assertRaises(v.CraftError):
            v.verify(argparse.Namespace(input=self.media, require_audio=False, lufs=float('nan'), peak=None))

    def test_network_playlist_protocol_rejected(self):
        playlist = self.p / 'remote.m3u8'
        playlist.write_text('#EXTM3U\n#EXT-X-TARGETDURATION:4\n#EXTINF:4,\nhttps://example.invalid/media.ts\n#EXT-X-ENDLIST\n')
        with self.assertRaises(v.CraftError) as error:
            v.probe(playlist)
        self.assertIn('whitelist', str(error.exception).lower())

    def test_symlink_output_rejected(self):
        link = self.p / 'link.mp4'
        link.symlink_to(self.media)
        with self.assertRaises(v.CraftError): v.output_path(link, True)

if __name__ == '__main__': unittest.main()
