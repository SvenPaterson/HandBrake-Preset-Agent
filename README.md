# HandBrake-Preset-Agent

A matched set of six HandBrake presets for ripping a personal Blu-ray
collection — three **archival-quality x265 keepers** and three **NVENC GPU
siblings** — plus the Python tooling that builds and verifies them and a
pair of LLM prompts that act as the "agent" half of the workflow
(initial design + ongoing maintenance against new HandBrake / x265 / NVENC
releases).

**Priority is quality over file size.** A typical Blu-ray rip lands ~30%
smaller than the source MKV (vs. the 60–80% reduction most consumer
presets push). Storage is cheap; re-ripping the collection in five years
because the encodes were too aggressive is not.

> Most of this was vibe-coded over a weekend in the spirit of the 80/20
> rule. Suggestions for improving the compression ratio without sacrificing
> quality are very welcome.

## Result — dark-scene fidelity

A representative comparison from *Dune: Part Two*. A sub-crypt scene with
deep crushed shadows, a narrow shaft of warm light on weathered stone, and
large near-black regions — the exact failure mode that exposes banding and
blocky-blacks on weaker encoders.

| Source Blu-ray | BD Archive - Standard (x265, RF 18, tune=grain) |
|---|---|
| <img src="images/Dune%20-%20Part%202%20-%20Original.png" alt="Dune Part Two — original Blu-ray frame" width="450"> | <img src="images/Dune%20-%20Part%202%20-%20Archive%20Preset.png" alt="Dune Part Two — BD Archive preset output" width="450"> |

The encoded frame is visually indistinguishable from the source on a
calibrated display: stone texture and chisel marks in the lit band are
preserved, the deep shadow regions stay smooth (no contour banding, no
16×16 posterization in the blackest areas), and the warm-to-shadow
falloff stays a continuous gradient. Source ~31.9 GB → output ~22.3 GB.

---

## Quick start

Clone this repo, then preview what would change in your HandBrake config
before touching anything:

```powershell
python build_bd_archive.py --dry-run
```

No files are written. The script auto-detects your HandBrake config
directory, lists the six presets it would add, the legacy entries it
would remove, and (importantly) the existing custom presets it would
**preserve untouched**. If the plan looks right, drop `--dry-run` to
apply it.

---

## Install — adding these presets to your HandBrake

Four options, in increasing power. Quit HandBrake first — it overwrites
`presets.json` on exit, which can clobber edits made while it's running.

**HandBrake's config folder lives at:**

| OS | Path |
|---|---|
| Windows | `%AppData%\HandBrake\` |
| macOS | `~/Library/Application Support/HandBrake/` |
| Linux | `~/.config/ghb/` |

### Option A — Import via the HandBrake GUI (zero-friction, non-destructive)

No scripts, no Python.

1. Download [presets.json](presets.json) from this repo.
2. In HandBrake: **Presets** menu → **Import** → select the downloaded file.
3. The six BD presets appear in your Custom Presets list next to anything you already have.

If you only want the BD presets (not the stock HandBrake presets bundled
in this file), open the downloaded `presets.json` in a text editor and
delete every preset block except the six whose `PresetName` starts with
`BD Archive —` or `BD Casual —`, then import.

### Option B — Run the merge script (recommended for power users)

Safe by default: auto-backs-up your `presets.json` with a timestamp,
merges the six BD presets next to your existing customs, leaves
`settings.json` alone unless you ask otherwise.

```powershell
git clone https://github.com/<you>/HandBrake-Preset-Agent.git
cd HandBrake-Preset-Agent

python build_bd_archive.py --dry-run    # preview, write nothing
python build_bd_archive.py              # backup + merge
python verify_bd_archive.py             # confirm parity across the set
```

Useful flags:

| Flag | Effect |
|---|---|
| `--dry-run` | Print planned changes, write nothing. |
| `--presets-dir PATH` | Override the auto-detected HandBrake config dir. |
| `--set-default` | Also set HandBrake's default preset to `BD Archive - Standard`. Off by default. |
| `--no-backup` | Skip the timestamped `.bak-*` backup. Not recommended. |

Rollback (if something looks wrong):

```powershell
Copy-Item "$env:APPDATA\HandBrake\presets.json.bak-YYYYMMDD-HHMMSS" `
          "$env:APPDATA\HandBrake\presets.json" -Force
```

### Option C — Replace your entire HandBrake config

> **Warning:** `presets.json` is HandBrake's *entire* preset database —
> stock presets, your custom presets, folder structure, and the
> "default preset" pointer all live in one file. Replacing it wholesale
> wipes any custom presets you've built. Use this only on a fresh
> HandBrake install.

1. Back up first:
   ```powershell
   Copy-Item "$env:APPDATA\HandBrake\presets.json"  "$env:APPDATA\HandBrake\presets.json.mybackup"
   Copy-Item "$env:APPDATA\HandBrake\settings.json" "$env:APPDATA\HandBrake\settings.json.mybackup"
   ```
2. Copy this repo's [presets.json](presets.json) and (optionally)
   [settings.json](settings.json) into the HandBrake config dir,
   overwriting the originals.
3. Restart HandBrake.

### Option D — Fork the design

If you want to change the preset set itself (different RF, different
tune, different audio behavior), edit the `SHARED` dict and per-preset
overrides in [build_bd_archive.py](build_bd_archive.py), then run it
against your config (Option B). The script is the single source of
truth; `presets.json` is regenerated from it.

---

## What's in here

| File | Purpose |
|---|---|
| [presets.json](presets.json) | The live HandBrake preset database (all six BD presets at the top of Custom Presets, plus stock HandBrake presets). |
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
| **BD Archive - Standard** | grain | 18 | Auto | Live action, modern 3D CGI animation, full-frame IMAX (Avatar) — anything with a single fixed aspect ratio. ~85% of a typical library. |
| **BD Archive - Variable AR** | grain | 18 | **Disabled** | Films whose aspect ratio shifts mid-film: Oppenheimer (2.20↔1.43), The Dark Knight (2.40↔1.78), Dunkirk (2.20↔1.90), partial-IMAX MCU and Mission: Impossible titles. Cropping is disabled so the IMAX expansion frames render correctly. |
| **BD Archive - Animation 2D** | animation | 19 | Auto | Hand-drawn / cel animation only: Studio Ghibli, classic pre-Tangled Disney, hand-drawn anime. `tune=animation` includes subtle banding mitigation that matters on twilight skies and lantern gradients. **Not** for modern 3D CGI — that goes on Standard. |

### BD Casual (NVENC siblings)

GPU-accelerated companions to each x265 keeper. Same crop / audio /
subtitle / metadata behavior; only the encoder swaps. NVENC HEVC 10-bit,
slowest preset, CQ tuned per content type. ~10× faster than the x265
keeper.

| Preset | CQ | Cropping | Use for |
|---|---|---|---|
| **BD Casual - Standard (NVENC)** | 22 | Auto | Validation pass on a fresh rip before committing the ~2 hr keeper, OR acceptable-quality keeper for low-priority content (TV movies, throwaway releases). |
| **BD Casual - Variable AR (NVENC)** | 22 | Disabled | Same role as above for variable-AR titles. Also confirms the AR shifts and forced-sub burn-in behave correctly before committing the keeper. |
| **BD Casual - Animation 2D (NVENC)** | 23 | Auto | Same role as above for 2D animation. |

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
- **Audio — English tracks:** Auto Passthru for every English track on the source (main mix, commentary, descriptive audio). Allows DTS-HD MA, TrueHD (incl. Atmos), DTS, DTS:X (rides inside DTS-HD MA), LPCM (incl. PCM), FLAC, ALAC, AC3, E-AC3, AAC, MP2, MP3, Opus to pass through bit-exact.
- **Audio — fallback:** none. `AudioEncoderFallback` is `none`, so any non-passthru-eligible source track is dropped rather than re-encoded. The primary playback chain (Apple TV 4K → Denon X3700H eARC) decodes every codec in the passthru list directly, so a fallback would only ever apply to exotic disc audio that does not exist in this library.
- **Audio — other languages:** ignored.
- **Subtitles:** Foreign Audio Search burns in *forced* subs only (Na'vi in Avatar, Chakobsa in Dune, German/French in Inglourious Basterds). All full English PGS tracks pass through as selectable, toggleable subtitle tracks.
- **Chapters:** preserved from source.
- **Metadata:** passed through, including Dolby Vision RPU and HDR10+ dynamic metadata when present.
- **Filters:** none. No denoise, sharpen, deblock, grain synth, chroma smooth, detelecine, deinterlace, or colorspace conversion. Archival rips preserve source characteristics.

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
python build_bd_archive.py --dry-run    # preview
python build_bd_archive.py              # backup + merge
python verify_bd_archive.py             # parity audit
```

The builder writes a timestamped backup of `presets.json` before
mutating, so it's safe to rerun. `settings.json` is only touched if you
pass `--set-default`.

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

- HandBrake **1.10.x / 1.11.x** (current stable as of April 2026,
  presets schema `VersionMajor: 72`). The merge script warns but
  proceeds if it sees an unrecognized schema version.
- Cross-platform: the helper scripts auto-detect the HandBrake config
  dir per OS (Windows `%APPDATA%\HandBrake`, macOS
  `~/Library/Application Support/HandBrake`, Linux `~/.config/ghb`).
  Override with `--presets-dir` for non-default installs.
- Python 3.9+ (uses `pathlib`, `argparse`, f-strings; no third-party
  dependencies).

---

## License

Configuration files and helper scripts in this repo are released under the
MIT license. HandBrake itself is GPL — see the
[HandBrake project](https://handbrake.fr/) for the encoder.
