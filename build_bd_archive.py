"""
One-shot builder: insert "BD Archive" folder with 3 presets into presets.json,
remove "x265 Archive Film", flip "GPU H.265 to MKV".Default to false,
update settings.json defaultPreset and PresetExpandedStateList.

Run from the HandBrake user data folder.
"""
import json
import copy
from pathlib import Path

ROOT = Path(__file__).parent
PRESETS = ROOT / "presets.json"
SETTINGS = ROOT / "settings.json"

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
    # Dark-region banding mitigation. x265's default aq-mode=2 quantizes flat
    # dark regions aggressively, producing visible posterization on heavily-
    # graded shadows (confirmed on Dune Part 2 cave/cloak scenes vs source).
    #   aq-mode=3      variance AQ with explicit dark-region bias
    #   aq-strength    1.0 (default) is fine; 1.1 if banding persists
    #   psy-rdoq=2.0   stronger than tune=grain default; preserves shadow
    #                  micro-texture which perceptually masks any residual
    #                  banding. Costs ~5% bitrate, no encode-time penalty.
    # tune=grain already sets psy-rd=2.0 and no-strong-intra-smoothing, so
    # we don't restate those here.
    p["VideoOptionExtra"] = "aq-mode=3:psy-rdoq=2.0"
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
    "BD Archive — Standard",
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
    "BD Archive — Variable AR",
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
    "BD Archive — Animation 2D",
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
    "BD Casual — Standard (NVENC)",
    crop_mode=0,  # Automatic — mirrors Preset A
    cq=22,        # ~ x265 RF 18 perceptual target
    description="GPU NVENC HEVC 10-bit, slowest, CQ 22, auto-crop. "
                "Casual / validation encode for live-action / 3D CGI; ~12 min "
                "per Blu-ray. Visible banding on dark gradients vs x265 keeper.",
)
preset_e = make_nvenc_preset(
    "BD Casual — Variable AR (NVENC)",
    crop_mode=2,  # None — mirrors Preset B
    cq=22,
    description="GPU NVENC HEVC 10-bit, slowest, CQ 22, NO crop. "
                "Casual / validation encode for AR-shifting films "
                "(Oppenheimer, Dark Knight, Dunkirk); ~12 min per Blu-ray. "
                "Visible banding on dark gradients vs x265 keeper "
                "(confirmed on Avatar 2009 cryosleep / Tree of Souls).",
)
preset_f = make_nvenc_preset(
    "BD Casual — Animation 2D (NVENC)",
    crop_mode=0,  # Automatic — mirrors Preset C
    cq=23,        # Animation tolerates slightly higher CQ
    description="GPU NVENC HEVC 10-bit, slowest, CQ 23, auto-crop. "
                "Casual / validation encode for hand-drawn animation; ~10 min "
                "per Blu-ray. Risk of banding on twilight skies / lantern "
                "gradients vs x265 tune=animation keeper.",
)

# ---------- Mutate presets.json ----------
# NOTE: HandBrake 1.11 Windows GUI does NOT support nested folders inside
# "Custom Presets" — it silently strips the wrapper folder and rewrites the
# file on next launch. So we place the 6 presets flat at the top level of
# Custom Presets. The "BD Archive — " / "BD Casual — " name prefixes group
# them visually.
data = json.loads(PRESETS.read_text(encoding="utf-8"))

custom = next(p for p in data["PresetList"]
              if p.get("Folder") and p.get("PresetName") == "Custom Presets")

# Remove any prior "x265 Archive Film" or stale "BD Archive" wrapper folder
before = len(custom["ChildrenArray"])
custom["ChildrenArray"] = [
    e for e in custom["ChildrenArray"]
    if e.get("PresetName") not in ("x265 Archive Film", "BD Archive")
    and not (e.get("Folder") and e.get("PresetName", "").startswith(("BD Archive", "BD Casual")))
]
# Also remove any pre-existing flat BD Archive / BD Casual presets (idempotency)
custom["ChildrenArray"] = [
    e for e in custom["ChildrenArray"]
    if not (not e.get("Folder")
            and e.get("PresetName", "").startswith(("BD Archive — ", "BD Casual — ")))
]
print(f"Removed {before - len(custom['ChildrenArray'])} stale entries.")

# Flip GPU H.265 to MKV default off (no-op if already false)
for e in custom["ChildrenArray"]:
    if e.get("PresetName") == "GPU H.265 to MKV" and e.get("Default") is True:
        e["Default"] = False
        print("Flipped 'GPU H.265 to MKV'.Default -> false")

# Append the 6 presets flat (3 BD Archive x265 keepers + 3 BD Casual NVENC siblings)
custom["ChildrenArray"].extend([preset_a, preset_b, preset_c, preset_d, preset_e, preset_f])

PRESETS.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"presets.json: 6 BD Archive/Casual presets placed flat in Custom Presets. "
      f"Custom Presets.ChildrenArray length: {len(custom['ChildrenArray'])}")

# ---------- Mutate settings.json ----------
settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
old_default = settings.get("defaultPreset", "")
settings["defaultPreset"] = "BD Archive — Standard"

expanded = settings.get("PresetExpandedStateList", [])
# Remove obsolete "BD Archive" wrapper-folder entry if present
expanded = [x for x in expanded if x != "BD Archive"]
settings["PresetExpandedStateList"] = expanded

SETTINGS.write_text(
    json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print(f"settings.json: defaultPreset '{old_default}' -> "
      f"'{settings['defaultPreset']}', PresetExpandedStateList now: {expanded}")
