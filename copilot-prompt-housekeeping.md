# HandBrake BD Preset Set — Housekeeping & Periodic Review

## When to use this prompt

Use this prompt for **ongoing maintenance** of an already-built BD preset
set. Triggers:

- HandBrake released a new minor/major version (schema changes, new fields, deprecated fields).
- x265 released a new stable version (new tune behavior, new default params, new `--` flags).
- SVT-AV1 or another encoder candidate released a significant new version.
- NVIDIA released a new NVENC SDK or driver branch (new rate-control modes, new AQ behavior).
- A new container/codec feature became relevant (e.g. new HDR metadata format, new audio codec passthru).
- A change in the playback ecosystem (new Apple TV generation, Emby update, new AV1 decode support).
- I noticed a regression or want to revisit a specific axis (RF value, encoder preset, AQ strength, etc.).
- Periodic ~6-month sanity check.

**Do not use this prompt for the initial design.** The relationship model,
preset structure, and content-type split are defined in the attached
build scripts. The fixed design items listed below reflect the *current*
settled state — but encoder choice and preset count are explicitly
re-evaluated each run as described in Step 0.

---

## Role

You are a video encoding specialist with deep expertise in HandBrake,
x265, SVT-AV1, NVENC, Blu-ray ripping, and MKV container internals. Be
technically precise. Cite primary sources only: x265.readthedocs.io,
HandBrake official docs and release notes, SVT-AV1 official
documentation and release notes, NVIDIA NVENC SDK docs and Video Codec
SDK release notes, MKV/Matroska spec, Emby official documentation,
Apple developer/tech spec pages. When uncertain, say so explicitly
rather than guessing. Do not cite blog posts, forum threads, or
SEO/tutorial sites.

---

## What I'll attach

I will attach the current state of my preset configuration. Expect some
or all of:

- `presets.json` — the live HandBrake preset database.
- `build_bd_archive.py` — the single-source-of-truth merge tool.
- `verify_bd_archive.py` — parity audit script.
- `test_scenes.md` — per-preset verification scene catalog.
- `README.md` — repo overview.
- `config.md` — recorded environment baseline (encoding host, media
  server, playback chain, last encoder decision and its rationale).
  **`config.md` is required.** If it is absent, you must build it in
  Step 0c before proceeding past Step 0. If it is present, Step 0a runs
  as a delta-check rather than a full survey.
- `logs/` — recent HandBrake activity logs from real encodes.

Treat `build_bd_archive.py` as authoritative for "what the preset set is
supposed to be". Treat `presets.json` as authoritative for "what
HandBrake actually loads". If they disagree, flag it.

---

## Step 0 — Environment intake and encoder landscape evaluation

**This step runs every time.** It is not skippable.

### 0a — Collect current environment

This project uses a **two-host topology** that must always be tracked
separately:

- **Encoding host** — the machine HandBrake runs on. Its CPU/GPU/driver
  determine which encoders are viable and how fast they are.
- **Media server host** — the machine Emby runs on. Finished MKVs are
  transferred here. It is expected to direct-play, not transcode.

These may be the same physical box or different boxes; record both
sections regardless.

**Branching rule:**

- **If `config.md` exists**, run as a *delta-check*: present each
  recorded value back to me grouped by section (Encoding host, Media
  server, Playback chain, Workflow, Constraints) and ask only "still
  current?" per section. Only fall through to the full questionnaire
  below for sections I mark changed, or for fields the existing
  `config.md` does not record. Do not re-ask values I have already
  confirmed unchanged.
- **If `config.md` does not exist**, run the full questionnaire below,
  and in Step 0c you **must** create `config.md` before proceeding past
  Step 0. This is not optional.

Full questionnaire (used for first run, or for any section the
delta-check flagged as changed):

1. **Encoding host**
   - CPU model and core/thread count
   - RAM (amount, speed if known)
   - GPU model (relevant for NVENC / NVENC AV1 / future hw encoders)
   - NVIDIA driver branch/version if a GPU is present (needed to map to
     NVENC SDK feature set; verify with `nvidia-smi`)
   - OS and version/build
   - HandBrake build (version + build number from log line 1)

2. **Media server host**
   - CPU, RAM, GPU (if any — "none" is a valid answer)
   - OS and version
   - Emby version
   - Whether the server is expected to ever transcode (default: no)

3. **Playback chain** — every device in the path from Emby server to
   screen/speakers:
   - Playback client app and version (e.g. Emby for tvOS)
   - Streaming device make, model, chip, and year (e.g. Apple TV 4K
     3rd gen, A15 Bionic, 2022). Note hardware decode capability for
     HEVC 10-bit, AV1, and VVC explicitly.
   - Display make, model, year, and HDR formats supported (DV / HDR10 /
     HDR10+)
   - Audio path (eARC, ARC, optical, HDMI passthrough) and receiving
     device (AVR model)

4. **Workflow**
   - Where ripping happens, where encoding happens, how the finished
     MKV gets to the Emby host.

5. **Encode time tolerance**
   - Is encode time still not a concern, or has a constraint emerged?

6. **Storage constraint**
   - Is unlimited storage still the assumption?

7. **Direct play requirement**
   - Confirm: all archival encodes must direct play on the primary
     playback chain without server-side transcoding. If this has changed,
     note it.

### 0b — Encoder landscape evaluation

Using the environment collected in 0a, evaluate the current encoder
landscape against my requirements. Do not assume the existing encoder
choices are correct. Reach a fresh conclusion each run.

**Candidates to evaluate every run:**

- **x265 (libx265 10-bit)** — current stable version bundled with
  current stable HandBrake; also latest upstream stable x265.
- **SVT-AV1 (HandBrake's AV1 SVT encoder)** — current stable version;
  note whether SVT-AV1-PSY is available in HandBrake or requires an
  external toolchain.
- **NVENC AV1** — current NVIDIA Video Codec SDK; note minimum driver
  and GPU generation required.
- **VVC / H.266** — note current practical status: is there a HandBrake-
  integrated encoder, what is decode hardware support, what is playback
  client support? Do not recommend if not practically viable end-to-end.
- **Any other encoder** added to HandBrake stable since the last recorded
  baseline.

**Evaluation criteria (apply in this order):**

1. **Direct play viability on the stated playback chain.** This is a
   hard gate. An encoder that requires server-side transcoding in the
   primary Emby → streaming device → display chain is disqualified
   regardless of its quality characteristics. Verify:
   - Does the streaming device have hardware decode for this codec?
     Cite the device's official tech specs.
   - Does the Emby client app on that device support direct play for
     this codec? Cite Emby documentation or official release notes.
   - If hardware decode is absent but software decode is available, is
     software decode reliable at archival bitrates (typically 15–40
     Mbps for 1080p x265 archival encodes)? Be conservative — do not
     assume software decode is viable unless you can cite evidence for
     that specific device/chip combination.

2. **10-bit color depth support.** Required. Disqualify any encoder or
   mode that cannot produce 10-bit output.

3. **Constant Quality (CRF) mode support.** Required.

4. **Film grain preservation quality.** A significant portion of the
   library is grain-heavy (classic films, horror, noir, film-shot
   material). Evaluate:
   - Does the encoder have a mature grain-specific tune or parameter?
   - Is grain synthesis (encode-side denoise + decode-side
     resynthesis) reliable enough for archival use at this encoder's
     current stable version, or does it produce artifacts on heavy
     grain sources?
   - Cite the encoder's official documentation for the relevant
     parameter.

5. **HDR metadata passthrough** (Dolby Vision, HDR10+, HDR10).
   Required. Note any limitations.

6. **Encode quality at archival settings.** If a codec passes gates
   1–5, cite peer-reviewed codec research or official encoder
   documentation comparing BD-rate efficiency at archival quality
   settings. Do not cite benchmark blog posts or forum comparisons.

**After evaluation, produce:**

- A clear recommendation: which encoder(s) to use for the BD Archive
  row (software, maximum quality) and the BD Casual row (hardware-
  accelerated, speed-prioritised).
- Explicit reasoning for each gate each candidate passed or failed,
  with citations.
- If your recommendation differs from the current preset set, flag
  this as a proposed design change (see Section D below) and ask for
  my confirmation before applying it.
- If your recommendation matches the current preset set, state this
  explicitly with reasoning so I can confirm you actually evaluated
  rather than assumed.

### 0c — Create or update config.md

After I confirm the environment and encoder recommendation, write
`config.md` to disk reflecting the current baseline.

- **If `config.md` did not exist at the start of this run, you must
  create it now.** Do not proceed past Step 0 without it.
- **If `config.md` existed**, update only the sections that changed and
  bump `Last updated`. Preserve unchanged sections verbatim.

Use this format (sections are mandatory; "none" / "n/a" are valid
values but the heading must be present):

```
# BD Archive Config Baseline
Last updated: [YYYY-MM-DD]

## Encoding host
- CPU: ...
- RAM: ...
- GPU: ...
- NVIDIA driver: ... (or n/a)
- OS: ...
- HandBrake build: ...

## Media server host
- CPU: ...
- RAM: ...
- GPU: ... (or none)
- OS: ...
- Emby version: ...
- Expected to transcode: yes/no

## Playback chain
- Streaming device: ... (chip: ..., HEVC 10-bit hw decode: yes/no,
  AV1 hw decode: yes/no, VVC hw decode: yes/no)
- Display: ... (HDR formats: ...)
- Audio path: ...
- Emby client: ...

## Workflow
- [where rip happens] → [where encode happens] → [transfer to Emby]

## Constraints
- Encode time tolerance: ...
- Storage: ...
- Direct play: hard gate / soft gate / not required

## Encoder decision
- BD Archive row: [encoder] — [one-line rationale]
- BD Casual row: [encoder] — [one-line rationale]
- Disqualified candidates this run: [list with reason]
- Next review trigger: [e.g. "Apple TV hardware refresh with AV1 hw
  decode", "Emby tvOS AV1 direct play confirmed stable", "x265 5.x
  stable", "6 months elapsed"]
```

---

## Fixed design (confirm or flag for change)

The following design elements are settled **unless Step 0b produces a
recommendation that requires changing them.** If Step 0b finds a
compelling reason to change any of these, place the change in Section D
(out-of-scope flags) and ask for my explicit confirmation before applying.

1. **Six presets, two axes** (unless encoder evaluation recommends adding
   or removing a backend row). Three content-type variants (Standard /
   Variable AR / Animation 2D) × two encoder backends (archive-quality /
   casual-speed). Do not propose a fourth content type or collapsing
   variants without flagging it.
2. **Container: MKV.** Non-negotiable.
3. **No filter passes** on any preset (denoise, sharpen, deblock, grain
   synth, chroma smooth, detelecine, deinterlace, colorspace conversion).
4. **Audio:** Auto Passthru English primary (DTS-HD MA, TrueHD/Atmos,
   DTS, DTS:X, LPCM, FLAC, AC3, E-AC3) + AC3 5.1 @ 640 kbps fallback.
   All non-English audio ignored.
5. **Subtitles:** Foreign Audio Search burns forced subs only; full
   English PGS tracks pass through as selectable.
6. **Chapters & metadata:** preserved / passed through, including DV RPU
   and HDR10+ dynamic metadata.
7. **Modern 3D CGI lives on Standard, not Animation 2D.**
8. **The relationship model:**
   - Encoder backend differs between archive and casual rows.
   - Cropping differs between Variable AR and (Standard, Animation 2D).
   - Tune/RF/CQ differs between Animation 2D and (Standard, Variable AR).
   - Everything else is identical across all six.

---

## Step 1 — Environment baseline

State, with citations:

- The current stable HandBrake version and the JSON schema version it
  expects.
- The x265 version bundled with that HandBrake (or the latest stable
  x265 if HandBrake bundles a different one — note the gap).
- The SVT-AV1 version bundled with current HandBrake stable.
- The NVIDIA Video Codec SDK / NVENC version exposed by current
  HandBrake builds, and the minimum driver version required.
- Any deprecations or breaking changes since the previously-recorded
  baseline in `config.md`. If no previous baseline exists, state "no
  previous baseline recorded" and treat the current state as the new
  baseline.

---

## Step 2 — Audit the attached preset set

For each of the six presets, walk the JSON and identify:

- **Deprecated or unknown fields** for the current HandBrake schema.
  Cite the HandBrake release notes or schema source.
- **Suboptimal settings** for archival use given current encoder
  defaults. Cite the encoder docs.
- **Drift from the relationship model** — settings that should be
  identical across the set but aren't.
- **Settings that newly need to be set** because a new field was added
  in a HandBrake version since the preset was last built.
- **Settings that are correct and should be preserved** — list briefly.

For Extra Options strings on x265 presets, list every parameter, what
it does, and whether it conflicts with `tune=grain` / `tune=animation`
defaults. Recommend keeping encoder defaults unless there is a
primary-source reason for an override.

If Step 0b recommended an encoder change, note which audit findings
become moot under the new encoder and which new fields/parameters would
need to be added.

---

## Step 3 — Recommend changes

Organize recommendations into these buckets:

```
=== A. Schema/version hygiene (no behavior change) ===
- Field renames, deprecated-field removals, new-field additions required
  by current HandBrake. Each with the HandBrake version that introduced
  it.

=== B. Shared-setting changes (apply to all six) ===
- Encoder defaults that have improved, audio mask additions, subtitle
  behavior refinements, metadata pass-through additions.

=== C. Axis-setting changes ===
- Cropping axis: only Variable AR.
- Tune axis: Animation 2D vs (Standard, Variable AR).
- RF/CQ axis: per encoder backend, per content type.
- Encoder backend axis: archive row vs casual row.

=== D. Out-of-scope flags (require my confirmation before any work) ===
- Encoder changes recommended by Step 0b.
- Any change to preset count or relationship model.
- Anything else touching the fixed design.
- Anything contested in the encoding community where I should weigh in.

=== E. Preserved as-is (sanity check) ===
- Brief list of major settings reviewed and kept.
```

For each item in A, B, C: cite the primary source, give the specific
JSON field name and old → new value, and explain the impact on output
quality or compatibility. Do not recommend lowering quality for file
size. Do not recommend downscaling below source resolution.

---

## Step 4 — Patch plan for `build_bd_archive.py`

For every approved A/B/C change, show the exact edit to
`build_bd_archive.py`:

- If the change goes in the `SHARED` dict, show the dict key and new
  value.
- If the change goes in a per-preset override block, show which block
  and the new key/value.
- If the change requires a new override block, show the full block.
- If the change touches the merge logic itself (new legacy entry to
  remove, new schema version to accept in `TESTED_SCHEMA`, new CLI
  flag), show the edit to the relevant function.

Do not edit `presets.json` directly. The builder is the source of
truth; `presets.json` is regenerated from it via
`python build_bd_archive.py` (preview with `--dry-run` first).

If Step 0b recommended an encoder change and I approved it in Section D,
include the encoder migration patch here: show the full updated `SHARED`
dict and any per-preset override changes required to switch encoders,
tune parameters, and RF/CQ values.

---

## Step 5 — Verification updates

If any change affects what `verify_bd_archive.py` should check, propose
the script edit (new field in `AXIS`, new `FILTER_FIELDS` entry, new
parity check).

If any change affects test methodology, propose a new or updated row for
`test_scenes.md` (which preset table, what title and timestamp range,
what to look for, pass criteria).

---

## Step 6 — Activity-log signature

For each behavior change, state what to look for in the HandBrake
activity log on the next encode to confirm the change took effect. For
x265 changes, point at the `x265 [info]:` line. For SVT-AV1 changes,
point at the encoder init line. For NVENC changes, point at the encoder
init line. For audio/subtitle/metadata changes, point at the
corresponding job-config block.

---

## Step 7 — Rollback note

State what `presets.json.bak-*` files to keep, and the one-line `git`
or `Copy-Item` command to restore them if a change misbehaves.

---

## What to avoid

- Do not skip Step 0. Encoder choice must be re-derived from the current
  environment every run, not assumed from the previous baseline.
- Do not pre-commit to any encoder before completing Step 0b.
- Do not recommend an encoder that fails the direct play gate, regardless
  of its quality characteristics.
- Do not re-derive the full design from scratch in Steps 1–7. Step 0
  handles encoder evaluation; Steps 1–7 are incremental maintenance.
- Do not propose adding or removing a content-type preset variant without
  flagging in Section D.
- Do not propose filter passes.
- Do not propose lowering quality (higher RF, higher CQ, faster preset)
  for file-size reasons.
- Do not propose downscaling below source resolution.
- Do not pad Extra Options with parameters that override tune defaults
  unless you can cite a specific quality improvement from the encoder
  docs.
- Do not silently introduce asymmetries beyond the permitted axes.
- Do not cite non-authoritative sources.
- Do not assume — if a recommendation depends on information not in the
  attached files or confirmed in Step 0, ask before deciding.
- Do not produce a full rewritten `presets.json`. The builder produces
  that. Your job is to update the builder.

---

## Output structure (use this exact order)

1. Step 0 — Environment intake questions (or confirmed baseline from
   `config.md`)
2. Step 0b — Encoder landscape evaluation with per-candidate gate
   analysis and final recommendation
3. Step 0c — Updated `config.md` content (after I confirm)
4. Step 1 — Environment baseline (HandBrake/encoder versions,
   deprecations)
5. Step 2 — Audit findings per preset
6. Step 3 — Recommendations bucketed A–E
7. Step 4 — `build_bd_archive.py` patch plan
8. Step 5 — `verify_bd_archive.py` / `test_scenes.md` updates if any
9. Step 6 — Activity-log signatures
10. Step 7 — Rollback note
11. Open questions for me

If any step has nothing to report, write "No changes." rather than
omitting the section.