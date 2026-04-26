# HandBrake Archival Preset Set — Evaluation, Rebuild, and Sync

## Role

You are a video encoding specialist with deep expertise in HandBrake, x265, NVENC, Blu-ray ripping, and MKV container internals. Your responses must be technically precise, cite authoritative sources (x265.readthedocs.io, HandBrake official documentation, NVIDIA NVENC SDK docs), and avoid repeating common forum misinformation. When you are uncertain, say so explicitly rather than guessing.

## Context

I am building an archival-quality HandBrake preset **set of three** for ripping my personal Blu-ray collection. I need three presets that share most settings but differ along two specific axes: cropping behavior (for IMAX/variable aspect ratio content) and encoder tune (for traditional 2D animation).

I already have existing preset JSON file(s) that I will attach. I want you to evaluate them against current best practices, produce an improved matched set of three presets, and maintain them in sync going forward.

## The three presets

**Preset A: "BD Archive - Standard"**
- For live-action films and modern 3D CGI animation (Pixar, modern Disney, DreamWorks, Illumination, Sony Animation, etc.)
- Also used for films with visible grain, dark-heavy content, horror, noir, classic films
- Automatic cropping enabled — HandBrake removes black bars during encoding
- Tune: grain
- Use case: ~85% of a typical modern Blu-ray library

**Preset B: "BD Archive - IMAX/Variable"**
- For films with variable aspect ratio scenes (IMAX Enhanced releases, partially-IMAX-shot films like Oppenheimer, The Dark Knight, Dunkirk, recent MCU titles, recent Mission: Impossible titles)
- Cropping disabled — preserves source framing exactly, including black bars, so IMAX expansion scenes render correctly
- Tune: grain (same as Preset A)
- Use case: identified per-disc when I confirm IMAX content is present

**Preset C: "BD Archive - Animation 2D"**
- For traditional hand-drawn / cel animation: Studio Ghibli, classic Disney (pre-Tangled), hand-drawn anime, flat-shaded adult animation
- NOT for modern 3D CGI animation — that uses Preset A
- Automatic cropping enabled (traditional 2D animation on Blu-ray is fixed aspect ratio)
- Tune: animation
- Use case: specific subset of library with traditional 2D animated content

## The relationship between presets (this is a hard constraint)

The three presets share MOST settings. The only permitted differences are:

1. **Cropping settings differ between Preset B and (Preset A, Preset C).** Preset B has cropping disabled; A and C have automatic cropping enabled.

2. **Tune and RF differ between Preset C and (Preset A, Preset B).** Preset C uses `tune=animation` and RF 19; A and B use `tune=grain` and RF 18.

All other settings (video encoder, encoder preset, framerate mode, filters, audio, subtitles, chapters, metadata) must be identical across all three presets.

### Summary of permitted differences:

| Setting | Preset A (Standard) | Preset B (IMAX) | Preset C (Animation 2D) |
|---------|---------------------|-----------------|-------------------------|
| Cropping | Auto | Disabled | Auto |
| Tune | grain | grain | animation |
| RF value | 18 | 18 | 19 |
| All other settings | IDENTICAL | IDENTICAL | IDENTICAL |

## Sync requirement

This prompt will be reused across multiple iterations. When I bring it back with requests to modify the presets:

1. **Changes to "shared" settings must apply to all three presets simultaneously.** Shared settings are: video encoder, encoder preset, framerate mode, all filters, Extra Options, audio configuration, subtitle configuration, chapters, metadata.

2. **Changes to "axis" settings apply per the relationship table above.**
   - Cropping changes affect Preset B independently of A and C.
   - Tune or RF changes can affect (A+B) together with C changing independently, OR affect C independently of (A+B), depending on my request.

3. **If I request a change that breaks the relationship model** (e.g., changes a "shared" setting on only one preset, or introduces a fourth axis of difference), **flag this and ask me to confirm** before applying it. Do not silently diverge the presets.

4. **After producing the JSON, provide a diff summary** showing exactly what changed from the attached input presets, organized by:
   - Changes applied to all three presets (shared settings)
   - Changes applied along the cropping axis (Preset B vs A/C)
   - Changes applied along the tune/RF axis (Preset C vs A/B)
   - Any changes that break the relationship model, with reasoning and confirmation request

## My requirements (apply to ALL THREE presets as shared settings unless otherwise specified)

**Encoder priority:** Maximum archival quality. Encode time is not a concern. Final file should be visually transparent or near-transparent to the source Blu-ray on a high-end display at normal viewing distance.

**Container:** MKV. Non-negotiable. I need PGS subtitle support and lossless audio passthrough.

**Video encoding (shared except tune and RF):**
- H.265 10-bit software (x265), not NVENC. Archival quality over speed.
- Constant Quality mode (CRF/RF), not bitrate-targeted.
- Encoder Preset: Slower (or your recommendation if you have a primary-source-cited reason for a different value).
- No filter passes (denoise, sharpen, deblock, grain, chroma smooth, detelecine, deinterlace, chroma smooth, colorspace). Archival rips preserve source characteristics.
- Extra Options: only include parameters that do not conflict with the selected tune. If you recommend any, explain each parameter's effect and verify it does not override tune=grain or tune=animation defaults.

**Axis-specific video settings:**
- Preset A (Standard): `tune=grain`, RF 18, `PictureAutoCrop: true`
- Preset B (IMAX/Variable): `tune=grain`, RF 18, `PictureAutoCrop: false`, `PictureLooseCrop: false`
- Preset C (Animation 2D): `tune=animation`, RF 19, `PictureAutoCrop: true`

**Audio behavior (identical across all three):**
- Primary track: Auto Passthru for English, allowing DTS-HD MA, TrueHD, DTS, LPCM, FLAC, AC3, E-AC3 to pass through unmodified. DTS:X rides inside DTS-HD MA and passes through via the DTS-HD Passthru option.
- Secondary track: AC3 5.1 at 640 kbps as a compatibility fallback.
- All other language tracks: ignored.

**Subtitle behavior (identical across all three):**
- Burn in *forced* subtitles only (alien language, foreign-language dialog within an otherwise-English film).
- Simultaneously, all full English subtitle tracks pass through as selectable PGS tracks that can be toggled in the media player.
- This requires HandBrake's "Foreign Audio Search" behavior combined with subtitle track passthrough. Verify the exact setting names and values in the current HandBrake preset JSON schema.

**Chapters (identical):** Preserve chapter markers from the source.

**Metadata (identical):** Passthrough all source metadata.

## What I want you to produce

### 1. Evaluation of my attached preset(s)

Go through the existing preset(s) and identify:
- Settings that are already correct and should be preserved
- Settings that are suboptimal for archival quality and should change, with specific reasoning
- Settings that conflict with each other or with my stated requirements
- Any deprecated or incorrect JSON fields for the current HandBrake version

For each recommended change, cite the authoritative source (x265 docs URL, HandBrake docs URL, or NVIDIA SDK docs URL). If you're making a judgment call rather than citing a source, say so explicitly.

### 2. Rebuilt preset set JSON

Produce a single importable HandBrake preset JSON file containing all three presets (`PresetList` array with three entries). Match the schema version of HandBrake 1.9.x / 1.10.x (current stable as of 2026). If any field names are uncertain across versions, flag this.

The three presets must follow the relationship model defined above — shared settings identical, differences only along the two permitted axes.

### 3. Diff summary

After the JSON, provide a plaintext diff summary with this structure:

```
=== Changes to SHARED settings (applied to all three presets) ===
- [field name]: [old value] -> [new value]  (reason: ...)

=== Changes along CROPPING axis (Preset B only) ===
- [field name]: [old value] -> [new value]  (reason: ...)

=== Changes along TUNE/RF axis (Preset C only, or A+B together) ===
- [preset(s)] / [field name]: [old value] -> [new value]  (reason: ...)

=== Relationship model violations (flagged for my confirmation) ===
- [description, reasoning, explicit question for me]

=== Settings preserved from input ===
- [brief list of what was kept as-is]
```

### 4. Verification checklist

After the diff, provide a checklist I can use to verify the presets imported correctly, including:
- Exactly what dropdown values I should see in the HandBrake GUI after import for each preset (encoder, preset, tune, RF, cropping mode, audio tracks, subtitle behavior)
- What the Activity Log should show during an actual encode (x265 info line showing active parameters)
- A test encode protocol covering all three presets:
  - A 5-minute grainy/dark scene encoded with Preset A
  - A 5-minute variable aspect ratio scene encoded with Preset B (should retain IMAX frame expansion)
  - A 5-minute traditional 2D animation scene encoded with Preset C

### 5. Known limitations

Be explicit about:
- Any settings where "best practice" is genuinely contested in the encoding community
- Any behavior dependent on the Blu-ray source properly flagging forced subtitles
- HandBrake version-specific JSON schema issues
- Filesize overhead of preserving black bars in Preset B versus cropping in A/C
- The absence of rigorous empirical comparison data on `tune=animation` vs `tune=grain` vs `tune=none` for modern 3D CGI animation (acknowledge that placing modern CGI in Preset A rather than Preset C is a reasoned choice, not an empirically validated one)

## What to avoid

- Do not recommend lowering quality for file size reasons. I have storage.
- Do not recommend downscaling below source resolution.
- Do not recommend NVENC or hardware encoding. I want software x265.
- Do not pad Extra Options with parameters that override tune defaults unless you can justify why the override improves on the tune.
- Do not cite non-authoritative sources (random blog posts, SEO tutorial sites, commercial software vendor pages). Primary sources only: x265 docs, HandBrake docs, NVIDIA docs, or peer-reviewed codec research.
- Do not assume — if a setting depends on information not in my attached preset(s) or my requirements above, ask me before deciding.
- Do not introduce asymmetries between the three presets beyond the two permitted axes. If you think an additional asymmetry is warranted, flag it as a question, do not apply it silently.
- Do not suggest adding a fourth preset for modern 3D CGI animation. I have explicitly decided that content goes in Preset A (tune=grain).

## Attached

I will attach my current HandBrake preset JSON file(s). The attachment may be:
- A single preset (produce the set of three based on it)
- A pair of presets from a previous iteration (expand to three, adding Preset C based on the shared settings)
- A set of three from a previous iteration (treat as current baseline and apply my new requests as incremental changes, showing the diff)

Adapt accordingly.
