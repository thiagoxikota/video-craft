# Sound and rights

## Start with the genre

A warm event recap rarely benefits from horror-like risers, low booms and long threatening tails. A quiet interface demo may need no sound effects. Select sound by narrative role and emotional fit before comparing loudness or spectrum. No single number measures whether a sound fits the film.

Listen to the original clips. HVAC, wind, clothing noise and copyrighted music often become prominent when camera sound is boosted. Prefer a few clean authentic moments over a continuous dirty ambience bed. Do not synthesize or add applause or laughter to imply an audience reacted when they did not.

Use effects at structural moments. Give music, speech and effects different jobs; avoid having all three compete at full level. Duck the music under speech, then listen to the recovery. Preserve transients and intelligibility. A synthetic tone is appropriate for a test fixture, not a substitute for a convincing real-world recording.

## Use the right measurement

- Sample peak is not true peak. `volumedetect` does not measure inter-sample peaks.
- Probe for an audio stream before measuring. A silent/no-audio input must not become a passing measurement just because FFmpeg returned zero.
- Measure the final encoded file by decoding its audio. AAC can change peaks.
- Two-pass `loudnorm` helps target a full-program mix, but `linear=true` is a request; FFmpeg can choose dynamic processing. Listen for pumping or loss of musical shape.
- Do not apply full-program normalization to sparse no-music edits. Intentional silence should not cause aggressive gain on a few seconds of sound.
- `-14 LUFS` and `-2 dBTP` are adjustable workflow defaults here, not universal delivery standards. Follow a client's actual specification when provided.

The bundled `master` command refuses missing/silent audio, more than 12 dB requested gain, and final AAC measurements outside its targets. A refusal is useful information. Fix the source/mix rather than deleting the gate. The CLI does not automatically remove noise, mix a new bed or guarantee artistic mastering.

## Keep provenance

For each external asset record: local filename, creator, original URL, license name/version, license URL, access date, attribution required, modifications, and intended use. Keep receipts when relevant. A search result or third-party index is not evidence that an asset is licensed. Read the source page and the license; inspect whether it was removed or replaced. An HTTP 200 response alone proves nothing.

Prefer user-owned material or a clearly licensed source. CC0 does not automatically resolve privacy, publicity or trademark questions. CC-BY needs attribution; a restriction on commercial use must match the intended destination. Do not call a logo "free" because it is downloadable from an official site.

Commercial music offered inside a social app may have platform/account/territory limitations. Do not rip it or assume permission to distribute a baked-in copy elsewhere. When music will be added in-app, deliver a clean export without the music bed alongside an explicitly labeled review mix. Revisit sync if the final song differs.

Use [asset-sources.csv](../assets/asset-sources.csv) as an optional project manifest. Do not put private download tokens, signed URLs or client personal data into a public manifest.
