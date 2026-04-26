# HandBrake BD Archive / BD Casual Presets

A matched set of six HandBrake presets for ripping a personal Blu-ray
collection: three **archival-quality x265 keepers** and three **NVENC GPU
siblings** for fast validation passes and low-priority content. Plus the
Python tooling that builds and verifies them so the "shared" settings stay
truly shared.

This repo is the configuration directory contents from
`%AppData%\HandBrake` (Windows). It is published so other people building
archival rip workflows can crib from the design — copy the JSON into your
own `presets.json` or import it through the HandBrake GUI.

---

## What's in here

| File | Purpose |
|---|---|
| [presets.json](presets.json) | The live HandBrake preset database (all six BD presets live in the `BD Archive` folder, plus stock HandBrake presets). |
| [settings.json](settings.json) | HandBrake app settings (default preset, expanded folders). |
| [build_bd_archive.py](build_bd_archive.py) | Single-source-of-truth builder. Reconstructs the six BD presets from one `SHARED` dict + per-preset overrides, then patches them into `presets.json`. Run this when you want to change a shared setting across all six presets at once. |
| [verify_bd_archive.py](verify_bd_archive.py) | Audits the live `presets.json` to confirm the six presets only differ along the permitted axes (cropping, encoder backend, tune, RF). Fails loudly if drift creeps in. |
| [copilot-prompt-v3.md](copilot-prompt-v3.md) | **Initial build prompt.** The design spec used with an LLM to originally produce the preset set from scratch. Defines the relationship model. Read this first if you want to understand *why* the presets are shaped the way they are. |
| [copilot-prompt-housekeeping.md](copilot-prompt-housekeeping.md) | **Ongoing maintenance prompt.** Run this against the current `presets.json` periodically (new HandBrake version, new x265/NVENC build, new flags) to audit the existing presets and propose targeted updates without re-deriving the design from scratch. |
| [test_scenes.md](test_scenes.md) | Reference Blu-ray scenes for verifying each preset (banding torture tests, IMAX aspect-ratio shifts, forced-subtitle behavior, audio passthru). |
| [current_preset.json](current_preset.json) | Scratch export of whatever preset I'm currently editing. Not authoritative. |
| `*.archive`, `*.bak-*` | Timestamped backups of prior `presets.json` / `settings.json` states. |
| [logs/](logs/) | HandBrake activity logs from real encodes, kept for diagnosing regressions. |

---

## The six presets

All six live at the top level of HandBrake's Custom Presets list (no
subfolder). They split along two axes: **encoder backend** (x265 keeper vs
NVENC sibling) and **content type** (standard / variable AR / 2D
animation).

### BD Archive (x265 keepers)

The "real" rips. Software x265, 10-bit, slow preset, RF tuned per content
type. ~2 hr per Blu-ray on modern hardware. Goal: visually transparent to
the source on a calibrated display at normal viewing distance.

| Preset | Tune | RF | Cropping | Use for |
|---|---|---|---|---|
| **BD Archive — Standard** | grain | 18 | Auto | Live action, modern 3D CGI animation, full-frame IMAX (Avatar) — anything with a single fixed aspect ratio. ~85% of a typical library. |
| **BD Archive — Variable AR** | grain | 18 | **Disabled** | Films whose aspect ratio shifts mid-film: Oppenheimer (2.20↔1.43), The Dark Knight (2.40↔1.78), Dunkirk (2.20↔1.90), partial-IMAX MCU and Mission: Impossible titles. Cropping is disabled so the IMAX expansion frames render correctly. |
| **BD Archive — Animation 2D** | animation | 19 | Auto | Hand-drawn / cel animation only: Studio Ghibli, classic pre-Tangled Disney, hand-drawn anime. `tune=animation` includes subtle banding mitigation that matters on twilight skies and lantern gradients. **Not** for modern 3D CGI — that goes on Standard. |

### BD Casual (NVENC siblings)

GPU-accelerated companions to each x265 keeper. Same crop / audio /
subtitle / metadata behavior; only the encoder swaps. NVENC HEVC 10-bit,
slowest preset, CQ tuned per content type. ~10× faster than the x265
keeper.

| Preset | CQ | Cropping | Use for |
|---|---|---|---|
| **BD Casual — Standard (NVENC)** | 22 | Auto | Validation pass on a fresh rip before committing the ~2 hr keeper, OR acceptable-quality keeper for low-priority content (TV movies, throwaway releases). |
| **BD Casual — Variable AR (NVENC)** | 22 | Disabled | Same role as above for variable-AR titles. Also confirms the AR shifts and forced-sub burn-in behave correctly before committing the keeper. |
| **BD Casual — Animation 2D (NVENC)** | 23 | Auto | Same role as above for 2D animation. |

The known regression vs x265 is dark-gradient banding (most visible on
Avatar 2009 cryosleep / Tree of Souls scenes). Bright daytime live action,
animation without twilight skies, and dialogue-heavy material look
indistinguishable from the keeper at normal viewing distance. See
[test_scenes.md](test_scenes.md#banding-hunt--bd-casual-nvenc-vs-bd-archive-x265-avatar-2009-dark-scenes)
for the full A/B protocol.

---

## Shared behavior (identical across all six presets)

These are the settings the `verify_bd_archive.py` audit enforces as
identical across the entire set:

- **Container:** MKV. Non-negotiable — needed for PGS subtitles and lossless audio passthru.
- **Audio — primary track:** Auto Passthru for English. Allows DTS-HD MA, TrueHD (incl. Atmos), DTS, DTS:X (rides inside DTS-HD MA), LPCM, FLAC, AC3, E-AC3 to pass through bit-exact.
- **Audio — secondary track:** AC3 5.1 @ 640 kbps as a compatibility fallback for clients that can't decode the lossless track.
- **Audio — other languages:** ignored.
- **Subtitles:** Foreign Audio Search burns in *forced* subs only (Na'vi in Avatar, Chakobsa in Dune, German/French in Inglourious Basterds). All full English PGS tracks pass through as selectable, toggleable subtitle tracks.
- **Chapters:** preserved from source.
- **Metadata:** passed through, including Dolby Vision RPU and HDR10+ dynamic metadata when present.
- **Filters:** none. No denoise, sharpen, deblock, grain synth, chroma smooth, detelecine, deinterlace, or colorspace conversion. Archival rips preserve source characteristics.

---

## Result — dark-scene fidelity

A representative comparison from *Dune: Part Two*. Frame grab from a sub-
crypt scene with deep crushed shadows, a narrow shaft of warm light on
weathered stone, and large near-black regions — the exact failure mode
that exposes banding and blocky-blacks on weaker encoders.

| Source Blu-ray | BD Archive — Standard (x265, RF 18, tune=grain) |
|---|---|
| ![Dune Part Two — original Blu-ray frame](images/Dune%20-%20Part%202%20-%20Original.png) | ![Dune Part Two — BD Archive preset output](images/Dune%20-%20Part%202%20-%20Archive%20Preset.png) |

The encoded frame is visually indistinguishable from the source on a
calibrated display: stone texture and chisel marks in the lit band are
preserved, the deep shadow regions stay smooth (no contour banding, no
16×16 posterization in the blackest areas), and the warm-to-shadow
falloff stays a continuous gradient. This is the bar the BD Archive
presets are tuned to clear.

**File size for that fidelity:** the source MKV rip was ~31.9 GB; the
BD Archive — Standard re-encode came in at ~22.3 GB. That's roughly a
**30% reduction** (compression ratio ~0.70), which is modest by
consumer-encoding standards — most "good enough" presets push 60–80%
reduction. That's the explicit trade-off here: quality is prioritized
over file size. Storage is cheap; re-ripping the entire collection in
five years because the encodes were too aggressive is not.

---

## Why this design

A few load-bearing decisions worth calling out, since they're the most
common things people argue about:

1. **x265 over NVENC for keepers.** NVENC 10-bit + AQ is dramatically
   better than the legacy 8-bit NVENC era, but still measurably behind
   x265 `tune=grain` on the worst dark gradients. For an archival rip
   that's expected to outlive several display upgrades, encode time isn't
   the constraint — quality is.
2. **A separate Variable AR preset instead of just "always disable
   crop".** Auto-crop is genuinely useful on the ~95% of discs with fixed
   aspect ratios; it removes the black bars without touching active
   picture, saving disk space and avoiding pillarbox/letterbox confusion
   on player UIs. Disabling crop globally to handle the IMAX edge case
   would be lazy. The cost of maintaining two presets is one extra click
   per disc when I know IMAX content is present.
3. **Modern 3D CGI lives on Standard, not Animation 2D.** `tune=animation`
   is designed for flat-shaded cel animation (large solid color regions,
   sharp line art). Modern CGI from Pixar / DreamWorks / modern Disney
   has film-like grain structure, complex lighting, and photographic
   motion blur — closer to live action than to 2D animation. This is a
   reasoned choice, not an empirically validated one.
4. **No filter passes.** Filters are presentation-layer decisions. An
   archival rip should preserve source characteristics so the filter
   choice can be made (and re-made) at playback time by the player or a
   transcode profile.
5. **Forced-only burn + full-track passthru.** Burning forced subs handles
   alien-language and foreign-dialog scenes without requiring viewers to
   manually toggle subtitles mid-film. Keeping the full English PGS
   tracks selectable handles the "watching with the hard of hearing"
   case. Both, not either.
6. **The relationship model is enforced by tooling.** `build_bd_archive.py`
   builds all six presets from one `SHARED` dict plus per-preset
   overrides, and `verify_bd_archive.py` audits the live JSON to confirm
   no setting drifted off-axis. This catches the failure mode where you
   tweak one preset in the GUI, forget to mirror it to the other five,
   and discover six months later that your library has subtle
   inconsistencies.

---

## Workflow

**To rebuild the presets after editing `build_bd_archive.py`:**

```powershell
cd $env:APPDATA\HandBrake
python build_bd_archive.py
python verify_bd_archive.py
```

The builder writes a timestamped backup of `presets.json` and `settings.json`
before patching, so it's safe to rerun.

**To rip a Blu-ray:**

1. Identify content type (standard / variable AR / 2D animation).
2. Pick the matching **BD Casual (NVENC)** preset, run a ~10–15 min
   validation encode, scrub for crop / audio / subtitle / AR-shift
   correctness.
3. If validation passes and the title is a keeper, switch to the matching
   **BD Archive (x265)** preset and queue the full encode.
4. If it's low-priority content, the BD Casual output *is* the keeper.

See [test_scenes.md](test_scenes.md) for the per-preset verification scene
catalog.

---

## Compatibility

- HandBrake **1.9.x / 1.10.x** (current stable as of 2026). The JSON
  schema occasionally adds fields between minor versions; the builder is
  conservative and only sets fields HandBrake recognizes.
- Windows paths assumed in the helper scripts (`%AppData%\HandBrake`).
  Trivially portable to macOS (`~/Library/Application Support/HandBrake`)
  or Linux (`~/.config/ghb`) — adjust the path constants at the top of
  each script.

---

## License

Configuration files and helper scripts in this repo are released under the
MIT license. HandBrake itself is GPL — see the
[HandBrake project](https://handbrake.fr/) for the encoder.
