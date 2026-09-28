#!/usr/bin/env python3
"""Copy only the reviewed skill. No downloads, hooks, dependencies, or overwrites."""
import argparse
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--target', choices=['claude', 'codex'], default='claude')
p.add_argument('--scope', choices=['project', 'user'], default='project')
p.add_argument('--project', type=Path, default=Path.cwd())
p.add_argument('--dry-run', action='store_true')
a = p.parse_args()
source = Path(__file__).resolve().parent / 'skills' / 'video-craft'
base = Path.home() if a.scope == 'user' else a.project.expanduser().resolve()
parent = base / ('.claude' if a.target == 'claude' else '.codex') / 'skills'
target = parent / 'video-craft'
if target.exists() or target.is_symlink():
    p.error(f'Already exists: {target}. Inspect/back up the existing skill before choosing an update strategy.')
if not source.is_dir():
    p.error('Run install.py from a complete repository checkout.')
if a.dry_run:
    print(f'Would copy {source} to {target}')
else:
    parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print(f'Installed at {target}. Restart or reload your agent to discover the skill.')
