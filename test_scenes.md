# BD Archive / BD Casual - Test Scene Catalog

Test scenes for verifying behavior of the BD Archive (x265 keeper) and BD
Casual (NVENC sibling) presets. Confirm disc ownership / library rental
availability per title before running each test. Each scene targets ~5
minutes; trim with `--start-at duration:NNN --stop-at duration:300` in the
HandBrake CLI or the GUI Range selector.

## Preset → encoder map

| Preset | Encoder backend | Quality target | Typical encode time (1080p, 2 hr Blu-ray) |
|---|---|---|---|
| BD Archive - Standard | x265 medium, tune=grain | RF 18 | ~2 hr |
| BD Archive - Variable AR | x265 medium, tune=grain | RF 18 | ~2 hr |
| BD Archive - Animation 2D | x265 medium, tune=animation | RF 19 | ~1.5 hr |
| BD Casual - Standard (NVENC) | NVENC HEVC 10-bit, slowest | CQ 22 | ~12 min |
| BD Casual - Variable AR (NVENC) | NVENC HEVC 10-bit, slowest | CQ 22 | ~12 min |
| BD Casual - Animation 2D (NVENC) | NVENC HEVC 10-bit, slowest | CQ 23 | ~10 min |

**BD Archive (x265)** are the keepers — archival-grade, RF tuned per content
type, ~2 hr per Blu-ray.

**BD Casual (NVENC)** are the GPU siblings — same crop / audio / subtitle
behavior as their BD Archive counterpart, ~10x faster. Two use cases:
1. Validation pass on a fresh rip (audio passthru, subtitle burn-in, crop,
   AR shifts) before committing to the ~2 hr keeper.
2. Acceptable-quality keeper for low-priority content (TV movies, throwaway
   releases, anything you don't care about preserving at maximum fidelity).

**What to expect from BD Casual output:** visibly close to the x265 keeper
on bright / mid-tone content. The known regression vs x265 is dark-gradient
banding — confirmed visible on Avatar 2009 cryosleep and Tree of Souls
scenes (see banding hunt below). Bright daytime live-action, animation
without twilight skies, and dialogue-driven scenes generally look
indistinguishable from the keeper at normal viewing distance.

---

## Preset A — BD Archive - Standard
Live-action, modern 3D CGI, AND full-frame IMAX films (Avatar, Avengers Endgame
IMAX cut) — anything with a single, fixed aspect ratio. **x265 medium,
tune=grain, RF 18, auto-crop.** Auto-crop safely removes the black bars
without touching active picture. For a fresh disc, run `BD Casual - Standard
(NVENC)` first (~12 min) to validate audio / subs / crop, then commit to the
keeper (~2 hr).

| # | Title | Range | Stresses | Verify |
|---|-------|-------|----------|--------|
| A1 | Blade Runner 2049 | ~01:05:00–01:10:00 (~40–43%) (Wallace HQ) | Deep shadows, smooth amber gradients on rippling water, soft focus | No banding in gradients; no posterization in shadow detail; water highlights crisp |
| A2 | The Batman (2022) | ~00:02:30–00:07:30 (~1–4%) (opening crime scene) | Intentional heavy film grain, very low key lighting, dim warm interiors | Grain texture preserved (not smoothed into mush); no blocking in dark areas; red/orange light clean |
| A3 | Joker (2019) | ~00:33:00–00:38:00 (~27–31%) (bathroom dance) | Red-dominant lighting, sustained close-ups on skin, slow contrast ramps | Skin tones natural (not waxy); red channel not crushed; no chroma bleed on edges |
| A4 | Avatar (2009) | ~01:01:00–01:06:00 (~38–41%) (Jake's first night in the Pandoran forest) | Full-frame IMAX 1.78:1 (no AR shifts — auto-crops cleanly); sustained Na'vi dialogue with forced English subs; bioluminescent flora gradients in near-black backgrounds; fine CGI detail | Auto-crop removes black bars without touching picture; Na'vi forced subs burned in and legible; glowing flora gradients banding-free; no blocking in dark jungle; fine creature detail preserved |
| A5 | The Batman (2022) | ~00:01:30–00:03:00 (~1–2%) (rooftop POV intro) | **Grain regression test** for the move to plain `tune=grain` defaults (no `aq-mode` override on grain presets). Heavy uniform film grain over slow camera moves — the worst case for any grain-strobing risk if an aq-mode override creeps back in. | Compare a fresh encode against a prior encode of the same range. New encode (no override): grain field at least as dense, no visible frame-to-frame strobing/shimmering on the rooftop tiles, file size within ±10% of prior. Fail if shimmering is visible or grain looks softer. |

## Preset B — BD Archive - Variable AR
**ONLY** for films whose aspect ratio shifts mid-film (Oppenheimer 2.20↔1.43,
Dark Knight 2.40↔1.78, Dunkirk 2.20↔1.90). Full-frame IMAX films like
Avatar belong on Preset A — they auto-crop cleanly because there's nothing
outside the active frame to preserve. **x265 medium, tune=grain, RF 18, NO
crop.** For a fresh disc, run `BD Casual - Variable AR (NVENC)` first
(~12 min, also confirms AR shifts and forced-sub burn-in) then commit to the
keeper (~2 hr).

| # | Title | Range | Stresses | Verify |
|---|-------|-------|----------|--------|
| B1 | Oppenheimer | ~01:50:00–01:55:00 (~61–64%) (Trinity test) | AR transitions 2.20:1 ↔ 1.43:1 IMAX; extreme bright→dark dynamic range; bright sky banding risk | Full IMAX 1.43:1 frame expands top+bottom into the black bar area; no clipping; explosion gradient banding-free |
| B2 | The Dark Knight | ~00:01:30–00:06:30 (~1–4%) (opening bank heist) | 1.78:1 IMAX intercut with 2.40:1 standard scope | Aspect ratio toggles cleanly mid-shot; black bars appear/disappear at correct cuts |
| B3 | Dunkirk | ~00:35:00–00:40:00 (~33–38%) (Spitfire aerial) | IMAX 1.90:1; sustained sky gradients; extreme detail in clouds and aircraft | Sky gradient banding-free; fine aircraft detail preserved; no smearing on motion |

## Preset C — BD Archive - Animation 2D
Hand-drawn / cel animation. **x265 medium, tune=animation, RF 19, auto-crop.**
tune=animation includes subtle banding-mitigation that matters on twilight
skies and lantern gradients (Ghibli, anime night scenes). For a fresh disc,
run `BD Casual - Animation 2D (NVENC)` first (~10 min) to validate audio /
subs / crop, then commit to the keeper (~1.5 hr).

| # | Title | Range | Stresses | Verify |
|---|-------|-------|----------|--------|
| C1 | Spirited Away | ~00:30:00–00:35:00 (~24–28%) (bathhouse interior) | Large flat color blocks; intricate background line work; soft lantern gradients | Flat color regions clean (no mosquito noise around lines); line art crisp; lantern gradients banding-free |
| C2 | Princess Mononoke | ~00:22:00–00:27:00 (~16–20%) (forest spirits) | Subtle blue-green gradient skies; fine forest detail; glowing kodama | Sky gradients banding-free; glow effects don't ring; fine foliage not smoothed |
| C3 | Akira | ~00:08:00–00:13:00 (~6–10%) (bike chase opening) | Fast motion; neon reds/yellows; hand-drawn motion blur; dark night cityscape | Motion blur preserved (not over-sharpened); neon saturation accurate; dark backgrounds don't block |
| C4 | Spirited Away | ~01:15:00–01:18:00 (~62–64%) (twilight train sequence) | **Banding torture test** for tune=animation + `aq-mode=3` override. Sustained twilight sky gradient (deep blue → violet → black), reflected lantern halos on still water, near-uniform flat color regions. | Sky gradient banding-free — no visible stair-stepping on the blue→violet ramp; lantern halos smooth (no contour rings); flat water reflections clean (no posterization). Confirms `aq-mode=3` dark-bias is doing useful work on twilight content. |

---

## Banding hunt — BD Casual NVENC vs BD Archive x265 (Avatar 2009 dark scenes)

Use these scenes to A/B `BD Casual - Standard (NVENC)` against the
historical `GPU H.265 to MKV` output (8-bit NVENC, no AQ) and against the
`BD Archive - Standard` x265 keeper. Avatar 2009 is the canonical
banding torture test: sustained near-black backgrounds with subtle
blue/green bioluminescent gradients and slow contrast ramps — exactly where
8-bit NVENC posterized into "blocky blacks" historically. The new 10-bit
NVENC + AQ is a large step up from the legacy preset, but still measurably
behind x265 tune=grain on the worst dark gradients.

This section also doubles as the Animation 2D NVENC sanity check by proxy:
if the new NVENC settings hold up on Avatar's worst dark gradients, they
will trivially handle Spirited Away / Princess Mononoke / Akira.

Encode the same 1-2 minute clip with all three encoders, then scrub frame-by-
frame in mpv (`,` and `.` keys) on a calibrated display in a dim room.
Banding shows as concentric "contour lines" in what should be a smooth
gradient, most visible in dark blues, deep purples, and shadow-to-midtone
ramps.

Encode the same 1-2 minute clip with all three encoders, then scrub frame-by-
frame in mpv (`,` and `.` keys) on a calibrated display in a dim room.
Banding shows as concentric "contour lines" in what should be a smooth
gradient, most visible in dark blues, deep purples, and shadow-to-midtone
ramps.

| # | Title | Range | What to look for | Pass criteria |
|---|-------|-------|------------------|---------------|
| N1 | Avatar (2009) | ~00:00:30–00:02:00 (~0.3–1.2%) (cryosleep wake-up) | Very dark space-station interior; subtle blue ambient lighting; slow camera drift over near-black walls | No visible contour bands in the dark wall gradients; no blocky 16×16-pixel posterization in the blackest regions |
| N2 | Avatar (2009) | ~01:01:00–01:03:00 (~38–39%) (Jake's first night, bioluminescent forest) | Glowing flora at low brightness against deep-black jungle; slow pan across plants with subtle color falloff | Bioluminescent edges remain smooth (not stairstepped); no banding rings around glow sources; black background uniform (no patchy "noise islands") |
| N3 | Avatar (2009) | ~01:30:00–01:32:00 (~55–57%) (inside Hometree at night) | Dim warm firelight; large flat dark-brown bark surfaces; smoke and atmosphere | Bark surfaces show smooth lighting falloff (no banding); smoke gradients clean; no green/magenta tint shifts in shadow areas |
| N4 | Avatar (2009) | ~02:00:00–02:02:00 (~74–76%) (Tree of Souls, ceremony) | Ambient near-black with thousands of dim fiber-optic glow points; slow, sustained low-luminance gradient across entire frame | The single hardest banding test in the film. Glow points stay sharp; transitions between black and dim-purple/blue should be gradient, not stepped |
| N5 | Avatar (2009) | ~02:18:00–02:20:00 (~85–87%) (final battle, night air combat) | Fast motion + dark sky + tracer/explosion highlights | Dark sky uniform (no blocking from rate controller starving the background); explosion highlights don't ring; motion stays sharp |

**Comparison method:**
1. Encode the same range three ways: legacy `GPU H.265 to MKV`, new `BD Casual - Standard (NVENC)`, and `BD Archive - Standard` (x265 medium).
2. Open all three in mpv with `mpv --no-config file1 file2 file3` and use `_` to cycle between them at the same timestamp.
3. Pause on a representative dark frame and pixel-peek at 2-4× zoom (`Alt++` in mpv).
4. Expected ranking, worst → best banding handling: legacy 8-bit NVENC < BD Casual 10-bit NVENC w/ AQ < BD Archive x265 medium tune=grain. **Confirmed observation (Avatar 2009 cryosleep): even the new NVENC w/ AQ shows visible banding on dark blue gradients — this is the trade-off the BD Casual presets accept in exchange for ~10x speed.**

---

## Cross-cutting tests (run once on representative discs; preset-agnostic)

| # | Test | Method | Pass criteria |
|---|------|--------|---------------|
| X1 | Audio passthru bit-exact | Rip Dune: Part Two (TrueHD Atmos). Run `ffmpeg -i src.mkv -map 0:a:0 -c copy src.thd` and same on output. Compare SHA-256. Also run `mediainfo` on both. | SHA-256 of TrueHD streams matches exactly; mediainfo shows TrueHD format intact |
| X2 | DTS:X passthru | Rip Bohemian Rhapsody (DTS:X in DTS-HD MA). | mediainfo on output shows DTS-HD MA with DTS:X extension flag preserved |
| X3 | Multi-language passthru | Rip a Disney/Pixar disc with English + Spanish + French + commentary tracks. | Output track count and language tags match source |
| X4 | Forced subs visibility — artistic | Encode a Dune (2021) Chakobsa scene (~00:25:00 area) with Preset A or B. | Orange brushstroke subs appear burned AND a passthru English PGS track is also selectable in VLC and Emby Apple TV |
| X5 | Forced subs visibility — conventional | Encode an Inglourious Basterds segment (German/French dialog) with Preset A. | Forced English translations appear burned during foreign dialog only |
| X6 | Chapter preservation | Any disc. | `mkvmerge -i output.mkv` shows chapter marker count and timestamps matching source |
| X7 | Player compat sweep | One output file → play in VLC, MPC-HC, Plex (direct play to Apple TV), Emby (direct play to Apple TV), mpv. | No transcoding triggered on any client; all audio/sub tracks visible; forced burns display |
| X8 | Filesize sanity — x265 | Encode a 2-hour Blu-ray with Preset A. | Output ≈ 8–14 GB (heavy grain/action higher; animation lower). Outside 4–25 GB indicates a problem |
| X9 | Filesize sanity — NVENC | Encode a 2-hour Blu-ray with `BD Casual - Standard (NVENC)`. | Output ≈ 10–18 GB (NVENC ~25% larger than x265 at equivalent quality). Outside 5–30 GB indicates a problem |
| X10 | NVENC encoder verification | Run any NVENC preset; check Activity Log. | Look for `nvenc: version` line during init and `nvenc_h265_10bit` in the encoder line of the job config. Confirms GPU is being used. |

---

## Optional deeper tests (skip unless suspicious)

| # | Test | Method |
|---|------|--------|
| D1 | VMAF / SSIM vs source | `ffmpeg -i source.mkv -i output.mkv -lavfi libvmaf -f null -` on a 60s clip. Target VMAF ≥ 96 (transparent) for x265 keepers, ≥ 94 for NVENC |
| D2 | A/B frame compare | Extract PNGs at problem timestamps from source and output; view side-by-side |
| D3 | Activity log diff — x265 presets | Run Standard and Variable AR on the same source; diff the x265 info lines. Confirm only the auto-crop filter line differs (B has none) |
| D4 | Activity log diff — NVENC vs x265 | Run `BD Archive - Standard` and `BD Casual - Standard (NVENC)` on the same source. Confirm encoder swap (`x265_10bit` vs `nvenc_h265_10bit`), preset swap (`medium` vs `slowest`), and that audio/subtitle/crop blocks are byte-identical |

---

## Notes

- **Disc availability**: confirm per title before testing. Library rental is a valid substitute. If a stand-in is needed, replace with a disc you own that exhibits similar characteristics (note the substitution here).
- **Append over time**: when a disc reveals a new edge case (e.g., broken forced flagging, unusual aspect ratio handling), add a row to the appropriate preset's table.
- **HDR handling**: the BD Archive presets pass through Dolby Vision RPU and HDR10+ metadata via `VideoPasshtruHDRDynamicMetadata: "all"`. When you start ripping UHD discs, add a UHD-specific test row covering metadata preservation (`mediainfo` should show DV/HDR10+ in the output).
