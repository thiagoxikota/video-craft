# Release 1.0.1 validation

Validated 2026-09-28 on macOS with Python 3.14.7 and FFmpeg 9.0.1.

- 19 automated tests passed, using generated synthetic media and no downloaded footage.
- Literal home-directory paths tested through real `inspect` and `verify` subprocess calls and JSON timeline validation. This regression failed before the 1.0.1 fix.
- Actual render, mixed audio/silent clip assembly, image contact sheet and AAC mastering measured successfully.
- Invalid ranges, non-finite inputs, source replacement, existing outputs, symlinks, network playlists and shell-like filenames covered.
- Local skill installation into a clean project passed; repeat installation refused replacement.
- Skill frontmatter validator passed.
- Claude plugin and marketplace manifests passed `claude plugin validate` without warnings.
- Marketplace registration and plugin installation passed in an isolated Claude configuration. The initial installed plugin appeared enabled at version 1.0.0; 1.0.1 preserves the package structure and updates path handling.
- Generated contact sheet opened and visually inspected. It is a technical fixture, not an artistic showcase.
- Local Markdown reference links checked. Public package checked for private machine paths, credential patterns and media assets.

Run the current suite:

```bash
python3 -m unittest discover -s tests -v
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
```

CI runs the media tests on Ubuntu with Python 3.10 and 3.12. Its status, not this historical note, indicates whether the latest commit passed there.

Limits: no end-to-end model quality evaluation, full human listening session, Windows test, Claude web/Cowork render test, screen-reader review or formal security/accessibility certification was performed. Remotion is optional guidance, not a bundled/tested composition. Installation success does not mean every environment supplies FFmpeg or permits media execution.
