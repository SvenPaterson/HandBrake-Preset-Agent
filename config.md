# BD Archive Config Baseline

Last updated: 2026-04-26

This baseline records the **two-host topology** used for the BD preset
set: encoding happens on a Windows PC, finished MKVs are transferred to
a separate Unraid box that hosts Emby. Both hosts are tracked here
because encoder evaluation depends on the encoding host's CPU/GPU/driver
while the direct-play gate depends on the playback chain hanging off the
Emby host.

---

## Encoding host (Windows PC)

- **CPU:** AMD Ryzen 7 9700X (8C / 16T, Zen 5)
- **RAM:** 32 GB G.Skill F5-6000J3636F16G (DDR5-6000, CL36)
- **GPU:** NVIDIA GeForce RTX 5070 Ti (Blackwell, 9th-gen NVENC)
- **NVIDIA driver:** 595.97 (verify with `nvidia-smi`; needs to expose
  NVENC SDK 13.0 and Blackwell-class encode features)
- **OS:** Windows 11, build 26200 (10.0.26200)
- **HandBrake build:** 1.11.1 (2026032200), official Windows x86_64.
  Activity logs confirm `nvenc: version 13.0 is available` and
  `HEVC encoder version 4.1+222-afa0028` (libx265 10-bit).

This host runs both rip and encode. NVENC presets (BD Casual row) use
this GPU; x265 presets (BD Archive row) use this CPU.

## Media server (Unraid host)

- **CPU:** Intel i5-4460 (4C / 4T, Haswell)
- **RAM:** 16 GB DDR3
- **GPU:** none (no discrete GPU; iGPU not used for transcode)
- **OS:** Unraid 7.2.3
- **Emby version:** latest stable

This host stores the finished MKVs and serves them to the playback
chain. It is **not expected to transcode** — the direct-play gate below
must hold so this host only muxes/streams.

## Playback chain

- **Streaming device:** Apple TV 4K 3rd gen (chip: A15 Bionic, 2022)
  - HEVC 10-bit hardware decode: yes (Main 10, up to 4K60)
  - AV1 hardware decode: **no** (A15 has no AV1 hw decoder)
  - VVC / H.266 hardware decode: no
- **Display:** LG OLED C6H (2026) — Dolby Vision, HDR10, HDR10+
- **Audio path:** Apple TV → LG C6H → eARC → Denon AVR-X3700H.
  Lossless passthru capable: TrueHD/Atmos, DTS-HD MA, DTS:X (via
  carriage formats supported by ATV/AVR pair).
- **Emby client:** Emby for tvOS, latest

## Workflow

- Rip on encoding PC → encode on encoding PC → transfer finished MKV to
  Unraid Emby share. No re-encode on the Unraid side.

## Constraints

- **Encode time tolerance:** 2–5 hours per movie is acceptable.
- **Storage:** effectively unlimited.
- **Direct play:** **hard gate.** Every archival output must direct
  play on the Apple TV 4K 3rd gen → LG C6H → Denon X3700H chain via
  Emby for tvOS, with no server-side transcode of video, audio, or
  subtitles in the primary case.

## Encoder decision

- **BD Archive row:** `x265_10bit` (libx265, 10-bit Main 10) — chosen
  for archival quality, mature `tune=grain` / `tune=animation`, full
  HDR10 / HDR10+ / Dolby Vision RPU passthru, native ATV hw decode.
- **BD Casual row:** `nvenc_h265_10bit` (NVIDIA NVENC HEVC 10-bit) —
  chosen for fast verification passes on the same RTX 5070 Ti, same
  decode path on ATV, supports HDR passthru.
- **Disqualified candidates (most recent evaluation):**
  - **AV1 (any encoder: SVT-AV1, NVENC AV1):** fails the direct-play
    gate. ATV 4K 3rd gen / A15 has no AV1 hardware decoder; software
    decode at archival bitrates is not viable on tvOS.
  - **VVC / H.266:** no HandBrake-integrated stable encoder; no ATV
    hardware decode; no Emby client direct-play support.
- **Next review trigger:** any one of —
  - Apple TV refresh with AV1 (or VVC) hardware decode confirmed in
    Apple's official tech specs.
  - Emby tvOS client confirms AV1 direct play in official release notes.
  - x265 5.x stable release.
  - NVIDIA driver branch change that alters NVENC SDK feature set.
  - 6 months elapsed since `Last updated`.
