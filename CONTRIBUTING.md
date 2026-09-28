# Contributing

Keep changes tied to an observable editing or delivery problem. Use synthetic fixtures or media you can legally redistribute, with clear provenance. Do not add client footage, tokens, machine-specific paths or anecdotes about private work.

Run `python3 -m unittest discover -s tests -v`. Add tests for meaningful behavior: media properties, missing/silent audio, invalid input, output preservation and installation. A regex matching a paragraph is not a behavioral test.

For skill changes, test with an actual representative request. Review what the agent produced, including the exported media. Keep the entry point concise and move conditional instructions to references. Do not turn one user's artistic preference into an absolute rule for every genre.

Describe the concrete problem, changed behavior, verification and any remaining limitation in the pull request. Contributions are under the repository's MIT license.
