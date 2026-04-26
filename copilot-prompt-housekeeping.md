# HandBrake BD Preset Set — Housekeeping & Periodic Review

## When to use this prompt

Use this prompt for **ongoing maintenance** of an already-built BD preset
set. Triggers:

- HandBrake released a new minor/major version (schema changes, new fields, deprecated fields).
- x265 released a new stable version (new tune behavior, new default params, new `--` flags).
- NVIDIA released a new NVENC SDK or driver branch (new rate-control modes, new AQ behavior, new tuning info).
- A new container/codec feature became relevant (e.g. new HDR metadata format, new audio codec passthru).
- I noticed a regression or want to revisit a specific axis (RF value, encoder preset, AQ strength, etc.).
- Periodic ~6-month sanity check.

**Do not use this prompt for the initial design.** That was done in
[copilot-prompt-v3.md](copilot-prompt-v3.md). The relationship model,
preset count, and content-type split are settled and out of scope here.
This prompt assumes the existing set is the baseline and changes are
incremental.

## Role

You are a video encoding specialist with deep expertise in HandBrake,
x265, NVENC, Blu-ray ripping, and MKV container internals. Be technically
precise. Cite primary sources only (x265.readthedocs.io, HandBrake
official docs and release notes, NVIDIA NVENC SDK docs and Video Codec
SDK release notes, MKV/Matroska spec). When uncertain, say so explicitly
rather than guessing. Do not cite blog posts, forum threads, or
SEO/tutorial sites.

## What I'll attach

I will attach the current state of my preset configuration. Expect some
or all of:

- `presets.json` — the live HandBrake preset database (six BD presets at the top of Custom Presets, plus stock HandBrake presets).
- `build_bd_archive.py` — the single-source-of-truth merge tool. Contains the canonical `SHARED` dict and per-preset overrides for all six presets. CLI: `--dry-run`, `--presets-dir PATH`, `--set-default`, `--no-backup`. Default behavior is non-destructive: timestamped backup of `presets.json`, merge BD presets next to existing customs, do not touch `settings.json`.
- `verify_bd_archive.py` — parity audit script. CLI: `--presets-dir PATH`.
- `test_scenes.md` — per-preset verification scene catalog.
- `README.md` — repo overview describing the design intent and install paths.
- `logs/` — recent HandBrake activity logs from real encodes.

Treat `build_bd_archive.py` as authoritative for "what the preset set is
supposed to be". Treat `presets.json` as authoritative for "what
HandBrake actually loads". If they disagree, flag it.

## The fixed design (do not propose changes to these)

These are settled. Reject or flag any suggestion that would alter them:

1. **Six presets, two axes.** Three content-type variants (Standard /
   Variable AR / Animation 2D) × two encoder backends (x265 keeper / NVENC
   sibling). Do not propose a fourth content type, a third backend, or
   collapsing variants.
2. **Container: MKV.** Non-negotiable.
3. **No filter passes** on any preset (denoise, sharpen, deblock, grain
   synth, chroma smooth, detelecine, deinterlace, colorspace conversion).
4. **Audio:** Auto Passthru English primary (DTS-HD MA, TrueHD/Atmos,
   DTS, DTS:X, LPCM, FLAC, AC3, E-AC3) + AC3 5.1 @ 640 kbps fallback. All
   non-English audio ignored.
5. **Subtitles:** Foreign Audio Search burns forced subs only; full
   English PGS tracks pass through as selectable.
6. **Chapters & metadata:** preserved / passed through, including DV RPU
   and HDR10+ dynamic metadata.
7. **Modern 3D CGI lives on Standard, not Animation 2D.**
8. **The relationship model:**
   - Encoder backend differs between BD Archive and BD Casual rows.
   - Cropping differs between Variable AR and (Standard, Animation 2D).
   - Tune/RF/CQ differs between Animation 2D and (Standard, Variable AR).
   - Everything else is identical across all six.

If you believe a fixed-design item should change because of a development
in the encoding ecosystem, **flag it as an out-of-scope question at the
end of your review** — do not silently include it in proposed changes.

## What I want you to do

### Step 1 — Environment baseline

State, with citations:

- The current stable HandBrake version and the JSON schema version it expects.
- The x265 version bundled with that HandBrake (or the latest stable x265 if HandBrake bundles a different one — note the gap).
- The NVIDIA Video Codec SDK / NVENC version exposed by current HandBrake builds, and the minimum driver version required.
- Any deprecations or breaking changes since the previously-recorded baseline. If a previous baseline isn't in the attached files, say "no previous baseline recorded" and treat the current state as the new baseline.

### Step 2 — Audit the attached preset set

For each of the six presets, walk the JSON and identify:

- **Deprecated or unknown fields** for the current HandBrake schema. Cite the HandBrake release notes or schema source.
- **Suboptimal settings** for archival use given current encoder defaults. Cite the encoder docs.
- **Drift from the relationship model** — settings that should be identical across the set but aren't. Use `verify_bd_archive.py` semantics (axis fields are: `PresetName`, `PresetDescription`, `PictureCropMode`, `VideoTune`, `VideoQualitySlider`, `Default`, plus the encoder swap fields between BD Archive and BD Casual rows).
- **Settings that newly need to be set** because a new field was added in a HandBrake version since the preset was last built (e.g. a new HDR metadata flag, a new subtitle behavior field).
- **Settings that are correct and should be preserved** — list briefly so I can confirm you actually inspected them, not just the changed ones.

For Extra Options strings on x265 presets, list every parameter, what it
does, and whether it conflicts with `tune=grain` / `tune=animation`
defaults. Recommend keeping `--` defaults unless there is a primary-source
reason for an override.

### Step 3 — Recommend changes

Organize recommendations into these buckets:

```
=== A. Schema/version hygiene (no behavior change) ===
- Field renames, deprecated-field removals, new-field additions required by
  current HandBrake. Each with the HandBrake version that introduced it.

=== B. Shared-setting changes (apply to all six) ===
- Encoder defaults that have improved, audio mask additions, subtitle
  behavior refinements, metadata pass-through additions.

=== C. Axis-setting changes ===
- Cropping axis: only Variable AR.
- Tune axis: Animation 2D vs (Standard, Variable AR).
- RF/CQ axis: per encoder backend, per content type.
- Encoder backend axis: BD Archive vs BD Casual.

=== D. Out-of-scope flags (require my confirmation before any work) ===
- Anything touching the fixed design above.
- Anything that would break the relationship model.
- Anything contested in the encoding community where I should weigh in.

=== E. Preserved as-is (sanity check) ===
- Brief list of major settings reviewed and kept.
```

For each item in A, B, C: cite the primary source, give the specific JSON
field name and old → new value, and explain the impact on output quality
or compatibility. **Don't recommend lowering quality for file size.** Do
not recommend NVENC over x265 for keepers, or downscaling, or hardware
encoding swaps for the BD Archive row.

### Step 4 — Patch plan for `build_bd_archive.py`

For every approved A/B/C change, show the exact edit to
`build_bd_archive.py`:

- If the change goes in the `SHARED` dict, show the dict key and new
  value.
- If the change goes in a per-preset override (the `make_preset` /
  `make_nvenc_preset` calls or the functions themselves), show which
  override block and the new key/value.
- If the change requires a new override block (e.g. a new field that only
  applies to NVENC presets), show the full block.
- If the change touches the merge logic itself (new legacy entry to
  remove, new schema version to accept in `TESTED_SCHEMA`, new CLI
  flag), show the edit to the relevant function (`plan_changes`,
  `apply_changes`, `check_schema`, `main`).

Do not edit `presets.json` directly in your patch plan. The builder is
the source of truth; `presets.json` is regenerated from it via
`python build_bd_archive.py` (preview with `--dry-run` first).

### Step 5 — Verification updates

If the change affects what `verify_bd_archive.py` should check, propose
the script edit (new field added to `AXIS`, new `FILTER_FIELDS` entry,
new parity check, etc.).

If the change affects test methodology, propose a new row for
`test_scenes.md` (which preset table, what title and timestamp range,
what to look for, pass criteria).

### Step 6 — Activity-log signature

For each behavior change, tell me what to look for in the HandBrake
activity log on the next encode to confirm the change took effect. For
x265 changes, point at the `x265 [info]:` line. For NVENC changes, point
at the encoder init line. For audio/subtitle/metadata changes, point at
the corresponding job-config block.

### Step 7 — Rollback note

State what `presets.json.bak-*` and `settings.json.bak-*` files I should
keep, and the one-line `git` or `Copy-Item` command to restore them if a
change misbehaves.

## What to avoid

- Do not re-derive the design from scratch. The initial-build prompt did that.
- Do not propose adding a fourth preset, removing a preset, or merging presets.
- Do not propose filter passes.
- Do not propose NVENC for the BD Archive row, or x265 for the BD Casual row.
- Do not propose lowering quality (higher RF, higher CQ, faster preset) for file-size reasons.
- Do not propose downscaling below source resolution.
- Do not pad Extra Options with parameters that override tune defaults unless you can cite a specific quality improvement from the x265 docs.
- Do not silently introduce asymmetries beyond the permitted axes.
- Do not cite non-authoritative sources.
- Do not assume — if a recommendation depends on information not in the attached files, ask before deciding.
- Do not produce a full rewritten `presets.json`. The builder produces that. Your job is to update the builder.

## Output structure (use this exact order)

1. Environment baseline (Step 1)
2. Audit findings per preset (Step 2)
3. Recommendations bucketed A–E (Step 3)
4. `build_bd_archive.py` patch plan (Step 4)
5. `verify_bd_archive.py` / `test_scenes.md` updates if any (Step 5)
6. Activity-log signatures to verify the changes (Step 6)
7. Rollback note (Step 7)
8. Open questions for me

If any step has nothing to report, write "No changes." rather than
omitting the section, so I can confirm you considered it.
