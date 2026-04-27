"""
Merge the BD Archive / BD Casual preset set into a HandBrake config.

Safe by default for third-party users:
  * Auto-detects the HandBrake config dir per OS (override with --presets-dir).
  * Writes a timestamped backup before mutating anything.
  * Only touches BD-prefixed presets and the legacy entries this script
    originally replaced. Your other custom presets are left alone.
  * Does NOT modify settings.json unless --set-default is passed.
  * --dry-run prints the planned changes without writing.

Usage:
    python build_bd_archive.py                  # safe merge into detected dir
    python build_bd_archive.py --dry-run        # preview only, no writes
    python build_bd_archive.py --presets-dir PATH
    python build_bd_archive.py --set-default    # also point HandBrake's
                                                # default preset at
                                                # 'BD Archive - Standard'
    python build_bd_archive.py --no-backup      # skip the .bak-* backup
"""
import argparse
import copy
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 on stdout/stderr so preset names (which contain em-dash) and
# arrow glyphs in progress output don't crash on Windows cp1252 consoles.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Tested HandBrake schema range. Outside this we warn but proceed.
# 72 corresponds to HandBrake 1.10.x / 1.11.x (current as of April 2026).
TESTED_SCHEMA = {"VersionMajor": (72, 72), "VersionMinor": (0, 0)}


def default_handbrake_dir() -> Path:
    """Return the canonical HandBrake config directory for the current OS."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("%APPDATA% not set; pass --presets-dir explicitly.")
        return Path(appdata) / "HandBrake"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "HandBrake"
    # Linux / other Unix — ghb is HandBrake's GTK frontend's config name
    return Path.home() / ".config" / "ghb"

# ---------- Canonical SHARED settings (single source of truth) ----------
SHARED = {
    "AlignAVStart": False,
    "AudioCopyMask": [
        "copy:aac",
        "copy:ac3",
        "copy:eac3",
        "copy:truehd",
        "copy:dts",
        "copy:dtshd",
        "copy:mp2",
        "copy:mp3",
        "copy:flac",
        "copy:opus",
        # PCM passthru added in HandBrake 1.11.0 — lets BD/HD-DVD LPCM tracks
        # pass through losslessly instead of being dropped or re-encoded.
        "copy:pcm",
        # ALAC passthru added in HandBrake 1.9.0 — rare on BD but harmless.
        "copy:alac",
    ],
    "AudioEncoderFallback": "none",
    # ["eng"] + behavior "all" => pass through every English audio track on the
    # source disc (5.1 main mix, commentary, descriptive audio, etc.). An
    # empty list combined with "all" silently degrades to "first track only"
    # in HandBrake, which is not what we want for archival rips.
    "AudioLanguageList": ["eng"],
    "AudioList": [
        {
            "AudioBitrate": 160,
            "AudioCompressionLevel": 0,
            "AudioEncoder": "copy",
            "AudioMixdown": "none",
            "AudioNormalizeMixLevel": False,
            "AudioSamplerate": "auto",
            "AudioTrackQualityEnable": False,
            "AudioTrackQuality": -1,
            "AudioTrackGainSlider": 0,
            "AudioTrackDRCSlider": 0,
        }
    ],
    "AudioSecondaryEncoderMode": False,
    "AudioTrackSelectionBehavior": "all",
    "AudioTrackNamePassthru": True,
    "AudioAutomaticNamingBehavior": "unnamed",
    "ChapterMarkers": True,
    "ChildrenArray": [],
    "Default": False,
    "FileFormat": "av_mkv",
    "Folder": False,
    "FolderOpen": False,
    "Optimize": False,
    "Mp4iPodCompatible": False,
    # PictureCropMode + crop offsets are AXIS settings (overridden per preset below)
    "PictureCropMode": 0,
    "PictureBottomCrop": 0,
    "PictureLeftCrop": 0,
    "PictureRightCrop": 0,
    "PictureTopCrop": 0,
    "PictureDARWidth": 0,
    "PictureDeblockPreset": "off",
    "PictureDeblockTune": "medium",
    "PictureDeblockCustom": "",
    "PictureDeinterlaceFilter": "off",
    "PictureCombDetectPreset": "off",
    "PictureCombDetectCustom": "",
    "PictureDeinterlacePreset": "default",
    "PictureDeinterlaceCustom": "",
    "PictureDenoiseCustom": "",
    "PictureDenoiseFilter": "off",
    "PictureSharpenCustom": "",
    "PictureSharpenFilter": "off",
    "PictureSharpenPreset": "medium",
    "PictureSharpenTune": "none",
    "PictureDetelecine": "off",
    "PictureDetelecineCustom": "",
    "PictureColorspacePreset": "off",
    "PictureColorspaceCustom": "",
    "PictureChromaSmoothPreset": "off",
    "PictureChromaSmoothTune": "none",
    "PictureChromaSmoothCustom": "",
    "PictureItuPAR": False,
    "PictureKeepRatio": True,
    "PicturePAR": "auto",
    "PicturePARWidth": 0,
    "PicturePARHeight": 0,
    "PictureWidth": 0,
    "PictureHeight": 0,
    "PictureUseMaximumSize": False,
    "PictureAllowUpscaling": False,
    "PictureForceHeight": 0,
    "PictureForceWidth": 0,
    "PicturePadMode": "none",
    "PicturePadTop": 0,
    "PicturePadBottom": 0,
    "PicturePadLeft": 0,
    "PicturePadRight": 0,
    "PicturePadColor": "black",
    "PresetDescription": "",
    "PresetName": "",  # set per preset
    "Type": 1,
    "SubtitleAddCC": False,
    "SubtitleAddForeignAudioSearch": True,
    "SubtitleAddForeignAudioSubtitle": False,
    "SubtitleBurnBehavior": "foreign",
    "SubtitleBurnBDSub": False,
    "SubtitleBurnDVDSub": False,
    "SubtitleLanguageList": ["eng"],
    "SubtitleTrackSelectionBehavior": "all",
    "SubtitleTrackNamePassthru": True,
    "VideoAvgBitrate": 0,
    "VideoColorRange": "auto",
    "VideoColorMatrixCode": 0,
    "VideoEncoder": "x265_10bit",
    "VideoFramerateMode": "vfr",
    "VideoGrayScale": False,
    "VideoScaler": "swscale",
    # 'medium' chosen over 'slower' for ~10x encode speedup at <1% quality
    # delta on 1080p Blu-ray sources. RF (quality target) and tune do most
    # of the perceptual heavy lifting; preset is mostly an efficiency knob.
    "VideoPreset": "medium",
    # VideoTune is an AXIS setting (overridden per preset below)
    "VideoTune": "grain",
    "VideoProfile": "auto",
    "VideoLevel": "auto",
    "VideoOptionExtra": "",
    "VideoQualityType": 2,
    # VideoQualitySlider is an AXIS setting (overridden per preset below)
    "VideoQualitySlider": 18,
    "VideoMultiPass": False,
    "VideoTurboMultiPass": False,
    "VideoPasshtruHDRDynamicMetadata": "all",
    "x264UseAdvancedOptions": False,
    "PresetDisabled": False,
    "MetadataPassthru": True,
}


def make_preset(name, *, crop_mode, tune, rf, default=False, description=""):
    p = copy.deepcopy(SHARED)
    p["PresetName"] = name
    p["PresetDescription"] = description
    p["PictureCropMode"] = crop_mode
    p["VideoTune"] = tune
    p["VideoQualitySlider"] = rf
    # VideoOptionExtra policy:
    #
    #   tune=grain     -> NO override. Trust x265's tune=grain defaults
    #                     completely (aq-mode=0, psy-rd=4.0, psy-rdoq=10.0,
    #                     --rc-grain). The previous aq-mode=3 override was
    #                     added for Dune Part 2 dark-region banding, but the
    #                     x265 docs explicitly warn that overriding aq-mode
    #                     while tune=grain is active carries a strobing risk
    #                     on heavy-grain static shots. Cleaner to trust the
    #                     tune profile and revisit per-title only if banding
    #                     reappears on a specific source.
    #
    #   tune=animation -> aq-mode=3. Animation has no grain-strobing concern
    #                     (no grain) and benefits from explicit dark-region
    #                     bias on twilight/lantern gradient material
    #                     (Ghibli, anime night scenes — see test scene C4).
    if tune == "animation":
        p["VideoOptionExtra"] = "aq-mode=3"
    else:
        p["VideoOptionExtra"] = ""
    p["Default"] = default
    return p


def make_nvenc_preset(name, *, crop_mode, cq, description=""):
    """GPU NVENC HEVC 10-bit preset — used for the BD Casual family.

    BD Casual presets are not archival keepers. They serve two purposes:
      1. Fast validation passes for fresh rips (audio passthru, subtitle
         burn-in, crop, AR handling) before committing to a full BD Archive
         x265 encode.
      2. Acceptable-quality keepers for content the user does not care about
         preserving with maximum fidelity (TV movies, throwaway content,
         direct-to-stream releases).

    Encoder: nvenc_h265_10bit, preset 'slowest'. Adaptive quantization extras
    (spatial-aq + temporal-aq + b-ref-mode=middle) enabled to take advantage
    of Blackwell's 9th-gen NVENC quality improvements. Even so, NVENC shows
    visible banding on dark-gradient torture scenes that x265 + tune=grain
    avoids — confirmed on Avatar 2009 cryosleep / Tree of Souls. For dark
    or grain-heavy content the user cares about, use BD Archive (x265).
    On RTX 50-series this finishes a 1080p Blu-ray in ~10-15 minutes vs
    ~2 hours for x265 medium.
    """
    p = copy.deepcopy(SHARED)
    p["PresetName"] = name
    p["PresetDescription"] = description
    p["PictureCropMode"] = crop_mode
    p["VideoEncoder"] = "nvenc_h265_10bit"
    p["VideoPreset"] = "slowest"
    p["VideoTune"] = ""  # NVENC has no equivalent of x265's tune=grain
    p["VideoQualitySlider"] = cq
    p["VideoOptionExtra"] = "spatial-aq=1:temporal-aq=1:b-ref-mode=middle"
    p["VideoMultiPass"] = False
    p["Default"] = False
    return p


preset_a = make_preset(
    "BD Archive - Standard",
    crop_mode=0,  # Automatic
    tune="grain",
    rf=18,
    default=True,
    description="Archival x265 10-bit, medium, RF 18, tune=grain, auto-crop. "
                "Live-action, modern 3D CGI, AND full-frame IMAX films "
                "(Avatar, Avengers Endgame IMAX cut) — anything with a "
                "single, fixed aspect ratio. Auto-crop safely removes the "
                "black bars without touching active picture.",
)
preset_b = make_preset(
    "BD Archive - Variable AR",
    crop_mode=2,  # None — preserves source framing for AR-shifting (IMAX) content
    tune="grain",
    rf=18,
    default=False,
    description="Archival x265 10-bit, medium, RF 18, tune=grain, NO crop. "
                "ONLY for films whose aspect ratio shifts mid-film "
                "(Oppenheimer 2.20↔1.43, Dark Knight 2.40↔1.78, Dunkirk "
                "2.20↔1.90). Auto-crop would chop the IMAX expansion frames.",
)
preset_c = make_preset(
    "BD Archive - Animation 2D",
    crop_mode=0,  # Automatic
    tune="animation",
    rf=19,
    default=False,
    description="Archival x265 10-bit, medium, RF 19, tune=animation, auto-crop. "
                "Hand-drawn / cel animation. tune=animation includes subtle "
                "banding-mitigation that NVENC cannot replicate on twilight "
                "skies / lantern gradients (Ghibli, anime night scenes).",
)
preset_d = make_nvenc_preset(
    "BD Casual - Standard (NVENC)",
    crop_mode=0,  # Automatic — mirrors Preset A
    cq=22,        # ~ x265 RF 18 perceptual target
    description="GPU NVENC HEVC 10-bit, slowest, CQ 22, auto-crop. "
                "Casual / validation encode for live-action / 3D CGI; ~12 min "
                "per Blu-ray. Visible banding on dark gradients vs x265 keeper.",
)
preset_e = make_nvenc_preset(
    "BD Casual - Variable AR (NVENC)",
    crop_mode=2,  # None — mirrors Preset B
    cq=22,
    description="GPU NVENC HEVC 10-bit, slowest, CQ 22, NO crop. "
                "Casual / validation encode for AR-shifting films "
                "(Oppenheimer, Dark Knight, Dunkirk); ~12 min per Blu-ray. "
                "Visible banding on dark gradients vs x265 keeper "
                "(confirmed on Avatar 2009 cryosleep / Tree of Souls).",
)
preset_f = make_nvenc_preset(
    "BD Casual - Animation 2D (NVENC)",
    crop_mode=0,  # Automatic — mirrors Preset C
    cq=23,        # Animation tolerates slightly higher CQ
    description="GPU NVENC HEVC 10-bit, slowest, CQ 23, auto-crop. "
                "Casual / validation encode for hand-drawn animation; ~10 min "
                "per Blu-ray. Risk of banding on twilight skies / lantern "
                "gradients vs x265 tune=animation keeper.",
)

# ---------- Merge logic (shared by --dry-run and real run) ----------

BD_PRESETS = [preset_a, preset_b, preset_c, preset_d, preset_e, preset_f]
BD_NAMES = [p["PresetName"] for p in BD_PRESETS]
LEGACY_NAMES = ("x265 Archive Film", "BD Archive")  # old wrapper folder + earlier preset
# Prefixes to clean up on every run. Both the new hyphen form and the legacy
# em-dash form (used in installs prior to April 2026) are removed so users
# upgrading from earlier versions of this script don't end up with duplicates.
BD_PRESET_PREFIXES = (
    "BD Archive - ", "BD Casual - ",
    "BD Archive \u2014 ", "BD Casual \u2014 ",
)


def ensure_custom_presets_folder(data: dict) -> dict:
    """Find the 'Custom Presets' folder; create it if missing."""
    for p in data.get("PresetList", []):
        if p.get("Folder") and p.get("PresetName") == "Custom Presets":
            return p
    folder = {
        "PresetName": "Custom Presets",
        "Folder": True,
        "FolderOpen": True,
        "Type": 0,
        "ChildrenArray": [],
    }
    data.setdefault("PresetList", []).append(folder)
    print("Note: 'Custom Presets' folder was missing; created it.")
    return folder


def plan_changes(custom: dict) -> dict:
    """Return a dict describing what would change (used by both modes)."""
    children = custom.get("ChildrenArray", [])
    to_remove_legacy_folder = [
        e["PresetName"] for e in children
        if e.get("Folder") and e.get("PresetName", "").startswith(("BD Archive", "BD Casual"))
    ]
    to_remove_legacy_preset = [
        e["PresetName"] for e in children
        if e.get("PresetName") in LEGACY_NAMES
    ]
    to_remove_existing_bd = [
        e["PresetName"] for e in children
        if not e.get("Folder")
        and e.get("PresetName", "").startswith(BD_PRESET_PREFIXES)
    ]
    will_flip_gpu_default = any(
        e.get("PresetName") == "GPU H.265 to MKV" and e.get("Default") is True
        for e in children
    )
    surviving = [
        e["PresetName"] for e in children
        if e.get("PresetName") not in to_remove_legacy_folder
        and e.get("PresetName") not in to_remove_legacy_preset
        and e.get("PresetName") not in to_remove_existing_bd
    ]
    return {
        "remove": to_remove_legacy_folder + to_remove_legacy_preset + to_remove_existing_bd,
        "add": BD_NAMES,
        "flip_gpu_default": will_flip_gpu_default,
        "surviving_user_presets": [n for n in surviving if n != "GPU H.265 to MKV"],
    }


def apply_changes(custom: dict) -> None:
    """Mutate custom['ChildrenArray'] in place per plan_changes()."""
    children = custom.get("ChildrenArray", [])
    children = [
        e for e in children
        if e.get("PresetName") not in LEGACY_NAMES
        and not (e.get("Folder") and e.get("PresetName", "").startswith(("BD Archive", "BD Casual")))
    ]
    children = [
        e for e in children
        if not (not e.get("Folder")
                and e.get("PresetName", "").startswith(BD_PRESET_PREFIXES))
    ]
    for e in children:
        if e.get("PresetName") == "GPU H.265 to MKV" and e.get("Default") is True:
            e["Default"] = False
    children.extend(BD_PRESETS)
    custom["ChildrenArray"] = children


def check_schema(data: dict) -> None:
    major = data.get("VersionMajor")
    minor = data.get("VersionMinor")
    if major is None:
        print("Warning: presets.json has no VersionMajor field; schema unknown.")
        return
    lo, hi = TESTED_SCHEMA["VersionMajor"]
    if not (lo <= major <= hi):
        print(f"Warning: presets.json VersionMajor={major} is outside tested range "
              f"{lo}\u2013{hi}. Proceeding, but field names may have shifted.")


def backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = path.with_name(path.name + f".bak-{stamp}")
    dest.write_bytes(path.read_bytes())
    return dest


# ---------- CLI ----------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge BD Archive / BD Casual presets into a HandBrake config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--presets-dir", type=Path, default=None,
        help="HandBrake config directory (default: auto-detect per OS).",
    )
    parser.add_argument(
        "--set-default", action="store_true",
        help="Also write settings.json: set defaultPreset to 'BD Archive - Standard' "
             "and clean PresetExpandedStateList. Off by default.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print planned changes without writing any files.",
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Skip the timestamped .bak-* backup before writing.",
    )
    args = parser.parse_args(argv)

    config_dir = args.presets_dir or default_handbrake_dir()
    presets_path = config_dir / "presets.json"
    settings_path = config_dir / "settings.json"

    if not presets_path.exists():
        print(f"ERROR: presets.json not found at {presets_path}", file=sys.stderr)
        print("Launch HandBrake at least once, or pass --presets-dir.", file=sys.stderr)
        return 2

    print(f"HandBrake config dir: {config_dir}")
    # utf-8-sig tolerates a BOM that some editors / PowerShell Set-Content
    # write; the json module rejects a BOM under plain utf-8.
    data = json.loads(presets_path.read_text(encoding="utf-8-sig"))
    check_schema(data)
    custom = ensure_custom_presets_folder(data)
    plan = plan_changes(custom)

    print("\n=== Planned changes to presets.json ===")
    print(f"  Remove ({len(plan['remove'])}): {plan['remove'] or 'none'}")
    print(f"  Add    ({len(plan['add'])}): {plan['add']}")
    if plan["flip_gpu_default"]:
        print("  Flip 'GPU H.265 to MKV'.Default \u2192 false")
    print(f"  Preserved user presets ({len(plan['surviving_user_presets'])}): "
          f"{plan['surviving_user_presets'] or 'none'}")

    if args.set_default:
        if settings_path.exists():
            s = json.loads(settings_path.read_text(encoding="utf-8-sig"))
            print("\n=== Planned changes to settings.json ===")
            print(f"  defaultPreset: {s.get('defaultPreset', '')!r} "
                  f"\u2192 'BD Archive - Standard'")
            obs = [x for x in s.get("PresetExpandedStateList", []) if x == "BD Archive"]
            if obs:
                print("  Remove obsolete 'BD Archive' from PresetExpandedStateList")
        else:
            print(f"\nWarning: --set-default given but {settings_path} doesn't exist; skipping.")

    if args.dry_run:
        print("\nDry run \u2014 no files written.")
        return 0

    # Real write path.
    if not args.no_backup:
        bak = backup(presets_path)
        print(f"\nBacked up presets.json \u2192 {bak.name}")

    apply_changes(custom)
    presets_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {presets_path} (Custom Presets.ChildrenArray length: "
          f"{len(custom['ChildrenArray'])})")

    if args.set_default and settings_path.exists():
        # Note: settings.json is intentionally NOT backed up. HandBrake
        # rewrites the entire file on every shutdown (run counter, MRU paths,
        # last-update-check timestamp, UI state), so any backup is stale
        # within one session and restoring it would actively roll back state.
        # The only field this script touches is defaultPreset (one line),
        # trivially reversible by hand or by re-running with --set-default.
        s = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        old_default = s.get("defaultPreset", "")
        s["defaultPreset"] = "BD Archive - Standard"
        s["PresetExpandedStateList"] = [
            x for x in s.get("PresetExpandedStateList", []) if x != "BD Archive"
        ]
        settings_path.write_text(
            json.dumps(s, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {settings_path} (defaultPreset: {old_default!r} \u2192 "
              f"{s['defaultPreset']!r})")

    print("\nDone. Restart HandBrake to see the new presets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

