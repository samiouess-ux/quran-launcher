"""Manifest-driven Quran video renderer with strict Arabic text preservation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import secrets
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features
from hashtag_strategy import build_hashtags
from validate_content_manifest import validate_content_manifest


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "IslamicTikTokAutomation/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def ffmpeg_text(value: str) -> str:
    return (value.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\'").replace("%", "\\%")
            .replace(",", "\\,").replace("[", "\\[").replace("]", "\\]"))


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


MAX_VIDEO_SECONDS = 40.0


def validate_video_duration(duration: float, maximum: float = MAX_VIDEO_SECONDS) -> None:
    """Reject non-finite, non-positive, or over-limit render durations."""
    if not math.isfinite(duration):
        raise SystemExit("Video duration must be a finite number.")
    if duration <= 0:
        raise SystemExit("Video duration must be positive.")
    if duration > maximum:
        raise SystemExit(
            f"Video duration {duration:.3f}s exceeds the {maximum:.0f}-second maximum; "
            "select a shorter contiguous verse passage before rendering."
        )


def validate_quran_audio_approval(audio: dict) -> None:
    """Allow approved audio or an explicitly rights-cleared review-only preview."""
    preview_only = audio.get("preview_only") is True
    approved = audio.get("approved_for_first_test_video", audio.get("approved", False)) is True
    if not approved and not preview_only:
        raise SystemExit("Audio is not marked approved. Refusing to render.")
    if preview_only and approved:
        raise SystemExit("A preview-only recording cannot be marked production-approved.")
    exact_recording_reviewed = audio.get("exact_recording_user_reviewed", False) or any(
        item.get("exact_recording_user_reviewed", False)
        for item in audio.get("license_research_candidates", [])
        if isinstance(item, dict)
    )
    if not exact_recording_reviewed and not preview_only:
        raise SystemExit("Exact recitation has not been user-reviewed. Refusing to render.")
    rights_verified = audio.get("rights_verified") or any(
        item.get("status", "").startswith("approved_")
        for item in audio.get("license_research_candidates", [])
        if isinstance(item, dict)
    )
    if not rights_verified:
        raise SystemExit("Reuse permission for the exact Quran recording is not documented.")


def create_arabic_overlay(title: str, verses: list[dict], destination: Path,
                           template: str = "ornate_gold_classic") -> None:
    """Render one exact Quran verse in one of four genuinely distinct layouts."""
    templates = {"ornate_gold_classic", "nature_clean", "minimal_mushaf", "cinematic_landscape"}
    if template not in templates:
        raise SystemExit(f"Unsupported visual template: {template}")
    if len(verses) != 1:
        raise SystemExit("Each screen must contain exactly one verse.")
    if not features.check("raqm"):
        raise SystemExit("Arabic rendering blocked: Pillow libraqm/RAQM is unavailable.")
    try:
        bold_path = subprocess.check_output(
            ["fc-match", "-f", "%{file}", "Amiri:style=Bold"], text=True
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit("Unable to locate the Amiri Bold font.") from exc
    if not bold_path or not Path(bold_path).is_file():
        raise SystemExit(f"Required Amiri Bold font is missing: {bold_path!r}")
    image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Restore the approved translucent emerald reading panel behind the
    # complete ayah layout. Keep the footage visible through the panel.
    panel_accent = (213, 221, 175)
    draw.rectangle((0, 0, 1080, 1920), fill=(18, 42, 34, 30))
    draw.rounded_rectangle(
        (82, 320, 998, 1600), radius=48,
        fill=(3, 12, 18, 148), outline=(*panel_accent, 175), width=2
    )

    palettes = {
        "ornate_gold_classic": ((231,190,103,255),(255,255,255,255)),
        "nature_clean": ((205,238,211,255),(255,255,255,255)),
        "minimal_mushaf": ((238,226,195,255),(255,255,245,255)),
        "cinematic_landscape": ((190,220,255,255),(255,255,255,255)),
    }
    accent, text_color = palettes[template]
    title_font = ImageFont.truetype(bold_path, 58 if template != "minimal_mushaf" else 52)
    if template == "ornate_gold_classic":
        outer = [(540,392),(575,410),(785,410),(815,430),(845,475),(815,520),
                 (785,540),(575,540),(540,558),(505,540),(295,540),(265,520),
                 (235,475),(265,430),(295,410),(505,410)]
        draw.line(outer+[outer[0]], fill=accent, width=4, joint="curve")
        for cx in (282,798):
            for angle in range(0,360,45):
                rad=math.radians(angle)
                px=cx+math.cos(rad)*10; py=475+math.sin(rad)*10
                draw.ellipse((px-5,py-5,px+5,py+5),outline=accent,width=2)
        title_y=475
    elif template == "nature_clean":
        # Keep the approved shared reading panel; do not draw a second title frame.
        draw.line((170,590,910,590),fill=accent,width=3)
        title_y=475
    elif template == "minimal_mushaf":
        draw.line((140,420,940,420),fill=accent,width=3)
        draw.line((140,535,940,535),fill=accent,width=3)
        draw.ellipse((520,463,560,503),outline=accent,width=2)
        title_y=475
    else:
        # Keep the approved shared reading panel; do not draw a second title frame.
        draw.line((120,600,960,600),fill=accent,width=2)
        title_y=475
    draw.text((540,title_y),title,font=title_font,fill=accent,anchor="mm",
              direction="rtl",language="ar",stroke_width=2,stroke_fill=(0,0,0,220))
    verse=verses[0]
    exact_text=verse.get("arabic")
    if not isinstance(exact_text,str) or not exact_text.strip():
        raise SystemExit("Invalid/empty Arabic verse text.")
    chosen=None
    for size in (76,72,68,64,60,56,52,48):
        font=ImageFont.truetype(bold_path,size)
        words=exact_text.split(" "); lines=[]; current=""
        for word in words:
            candidate=(current+" "+word).strip()
            if draw.textbbox((0,0),candidate,font=font,direction="rtl",language="ar")[2] <= 900:
                current=candidate
            else:
                if current: lines.append(current)
                current=word
        if current: lines.append(current)
        if len(lines)<=4:
            chosen=(font,lines); break
    if chosen is None:
        raise SystemExit("Verse cannot fit safely; refusing to clip Quran text.")
    font,lines=chosen
    line_height=font.size*1.75
    first_y=850-(len(lines)-1)*line_height/2
    for i,line in enumerate(lines):
        draw.text((540,first_y+i*line_height),line,font=font,fill=text_color,
                  anchor="mm",direction="rtl",language="ar",
                  stroke_width=2,stroke_fill=(0,0,0,220))
    number=str(verse["number"]).translate(str.maketrans("0123456789","٠١٢٣٤٥٦٧٨٩"))
    number_font=ImageFont.truetype(bold_path,34)
    if template == "ornate_gold_classic":
        cx,cy,radius=540,1110,34
        pts=[]
        for angle in range(0,360,15):
            r=radius if (angle//15)%2==0 else radius-6
            rad=math.radians(angle); pts.append((cx+math.cos(rad)*r,cy+math.sin(rad)*r))
        draw.line(pts+[pts[0]],fill=accent,width=3,joint="curve")
        draw.text((cx,cy),number,font=number_font,fill=accent,anchor="mm",direction="rtl",language="ar",
                  stroke_width=1,stroke_fill=(0,0,0,210))
    elif template == "nature_clean":
        draw.rounded_rectangle((485,1080,595,1140),radius=28,outline=accent,width=3)
        draw.text((540,1110),number,font=number_font,fill=accent,anchor="mm",direction="rtl",language="ar",
                  stroke_width=1,stroke_fill=(0,0,0,210))
    elif template == "minimal_mushaf":
        draw.text((540,1110),f"۞ {number} ۞",font=number_font,fill=accent,anchor="mm",direction="rtl",language="ar")
    else:
        draw.line((390,1110,690,1110),fill=accent,width=2)
        draw.text((540,1160),number,font=number_font,fill=accent,anchor="mm",direction="rtl",language="ar",
                  stroke_width=1,stroke_fill=(0,0,0,210))
    image.save(destination)

def create_english_overlay(verses: list[dict], destination: Path) -> None:
    """One translation per screen, wrapped with generous line spacing."""
    if len(verses) != 1:
        raise SystemExit("Each screen must contain exactly one translation.")
    font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font=ImageFont.truetype(font_path,34)
    image=Image.new("RGBA",(1080,1920),(0,0,0,0))
    draw=ImageDraw.Draw(image)
    lines=[]; current=""
    for word in verses[0]["english"].split():
        candidate=(current+" "+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2] <= 900:
            current=candidate
        else:
            if current: lines.append(current)
            current=word
    if current: lines.append(current)
    if len(lines)>5:
        raise SystemExit("Translation exceeds safe layout.")
    line_h=58
    y=1300-(len(lines)-1)*line_h/2
    for line in lines:
        draw.text((540,y),line,font=font,fill=(255,255,255,255),anchor="mm",
                  stroke_width=2,stroke_fill=(0,0,0,230))
        y+=line_h
    image.save(destination)



def probe_media_duration(path: Path) -> float:
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ], text=True).strip()
    duration = float(result)
    if not math.isfinite(duration) or duration <= 0:
        raise SystemExit(f"Invalid media duration for {path}: {duration}")
    return duration


def build_background_reel(
    candidates: list[dict], duration: float, work: Path, destination: Path
) -> list[str]:
    """Build a moving-video reel from multiple approved clips with soft crossfades."""
    if not math.isfinite(duration) or duration <= 0:
        raise SystemExit("Background duration must be a finite positive number.")
    if not candidates:
        raise SystemExit("No approved backgrounds are available for this render.")

    transition = 0.55
    prepared = []
    total_coverage = 0.0
    next_candidate_index = 0
    for index, candidate in enumerate(candidates):
        next_candidate_index = index + 1
        if total_coverage >= duration + transition * max(0, len(prepared) - 1):
            break
        candidate_id = candidate["id"]
        raw_path = work / f"background_source_{index}.mp4"
        try:
            download(candidate["direct_video_url"], raw_path)
            measured = probe_media_duration(raw_path)
        except Exception as exc:
            print(f"Skipping unusable background {candidate_id}: {exc}")
            continue
        if not math.isfinite(measured) or measured <= 0:
            print(f"Skipping background with unusable duration: {candidate_id}.")
            continue
        # Trust measured media duration, not catalog estimates. Loop only that
        # clip if it is shorter than the remaining reel, then transition onward.
        prepared.append((candidate_id, raw_path, measured))
        total_coverage += measured
        if measured < duration:
            # Loop this approved clip rather than fetching a second clip just
            # to fill the remaining seconds of the same narration.
            break

    if not prepared:
        raise SystemExit("No approved background has a usable positive duration.")

    # A lone short approved clip is intentionally looped below. Do not fetch
    # another candidate merely to fill its duration before applying that loop.
    single_clip_will_loop = len(prepared) == 1 and prepared[0][2] < duration

    # Keep enough source time to cover the final duration after crossfade overlap.
    while (not single_clip_will_loop
           and total_coverage - transition * (len(prepared) - 1) < duration):
        if next_candidate_index >= len(candidates):
            break
        candidate = candidates[next_candidate_index]
        raw_path = work / f"background_source_{next_candidate_index}.mp4"
        next_candidate_index += 1
        try:
            download(candidate["direct_video_url"], raw_path)
            measured = probe_media_duration(raw_path)
        except Exception as exc:
            print(f"Skipping unusable background {candidate['id']}: {exc}")
            continue
        if measured <= 0 or not math.isfinite(measured):
            continue
        prepared.append((candidate["id"], raw_path, measured))
        total_coverage += measured
        if measured < duration:
            # Prefer looping one approved clip over introducing an unnecessary
            # second scene solely to fill a short duration gap.
            break

    if len(prepared) == 1 and prepared[0][2] < duration:
        # A single approved clip may loop to cover the narration; keep its
        # measured source duration for validation, but render the full target.
        prepared[0] = (prepared[0][0], prepared[0][1], duration)
        total_coverage = duration
    if total_coverage - transition * (len(prepared) - 1) < duration:
        raise SystemExit("Approved moving backgrounds do not cover the full video duration.")

    inputs, filters = [], []
    for index, (_, path, clip_duration) in enumerate(prepared):
        inputs += ["-stream_loop", "-1", "-i", str(path)]
        filters.append(
            f"[{index}:v]trim=duration={clip_duration:.6f},setpts=PTS-STARTPTS,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,fps=30,format=yuv420p,settb=AVTB"
            f"[bg{index}]"
        )

    current = "bg0"
    elapsed = prepared[0][2]
    for index in range(1, len(prepared)):
        label = f"bgx{index}"
        offset = max(0.0, elapsed - transition * index)
        filters.append(
            f"[{current}][bg{index}]xfade=transition=fade:duration={transition:.3f}:"
            f"offset={offset:.6f}[{label}]"
        )
        current = label
        elapsed += prepared[index][2]

    filters.append(
        f"[{current}]trim=duration={duration:.6f},setpts=PTS-STARTPTS,"
        "format=yuv420p[outv]"
    )
    run([
        "ffmpeg", "-hide_banner", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[outv]", "-an", "-t", f"{duration:.6f}", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
        str(destination)
    ])
    actual_duration = probe_media_duration(destination)
    if actual_duration + 0.10 < duration:
        raise SystemExit(
            f"Looped background reel is too short ({actual_duration:.3f}s for {duration:.3f}s)."
        )
    ids = [item[0] for item in prepared]
    print("Moving video background sequence with crossfades:", ", ".join(ids))
    return ids



ARABIC_BACKGROUND_KEYWORDS = {
    "sea": ("البحر", "بحر", "البحار", "موج"),
    "mountains": ("الجبال", "جبل", "طور", "رواسي"),
    "desert": ("الصحراء", "رمال", "沙"),
    "river": ("نهر", "الأنهار", "أنهار", "ماء"),
    "sunset": ("غروب", "الشمس", "الشمس", "ليل"),
    "mosque": ("مسجد", "المساجد", "المسجد"),
    "nature": ("شجر", "أشجار", "نبات", "زرع", "جنة", "جنات"),
    "sky": ("سماء", "السماوات", "نجوم", "قمر"),
}

def infer_background_tags(arabic_text: str) -> set[str]:
    """Conservative keyword matching after removing Arabic diacritics for lookup only."""
    normalized = re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED]", "", arabic_text)
    return {tag for tag, words in ARABIC_BACKGROUND_KEYWORDS.items()
            if any(re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED]", "", word) in normalized
                   for word in words)}

def select_photo_for_scene(eligible: list[dict], arabic_text: str, rotation_key: str,
                           scene_index: int, used_ids: set[str]) -> dict:
    wanted = infer_background_tags(arabic_text)
    matching = [item for item in eligible
                if wanted.intersection(set(item.get("tags", []))) and item["id"] not in used_ids]
    pool = matching or [item for item in eligible if item["id"] not in used_ids]
    if not pool:
        pool = eligible
    return min(pool, key=lambda item: hashlib.sha256(
        f"{rotation_key}:{scene_index}:{item['id']}".encode("utf-8")).digest())

def build_photo_background_reel(
    candidates: list[dict], scenes: list[dict], duration: float, work: Path,
    destination: Path, rotation_key: str
) -> list[str]:
    """Choose a tag-matched photo per verse scene and crossfade on scene boundaries."""
    if not math.isfinite(duration) or duration <= 0:
        raise SystemExit("Photo background duration must be a finite positive number.")
    if not rotation_key.strip():
        raise SystemExit("Photo background rotation key must not be empty.")
    eligible = []
    for item in candidates:
        path = Path(item.get("local_path", ""))
        if path.is_file() and path.stat().st_size >= 50_000:
            eligible.append(item)
    if not eligible:
        raise SystemExit("No downloaded and verified photo backgrounds are available.")
    if not scenes:
        raise SystemExit("No timed verse scenes were supplied for photo backgrounds.")

    used_ids: set[str] = set()
    chosen, scene_durations = [], []
    for index, scene in enumerate(scenes):
        text = " ".join(str(v.get("arabic", "")) for v in scene.get("verses", []))
        item = select_photo_for_scene(eligible, text, rotation_key, index, used_ids)
        chosen.append(item)
        used_ids.add(item["id"])
        scene_durations.append(float(scene["duration"]))
    # Correct only accumulated timing round-off; the audio track remains untouched.
    scene_durations[-1] += duration - sum(scene_durations)
    if any(not math.isfinite(d) or d <= 0 for d in scene_durations):
        raise SystemExit("Every verse scene must have a positive duration.")
    transition = min(0.6, min(scene_durations) * 0.20) if len(chosen) > 1 else 0.0
    inputs, filters = [], []
    for index, (item, scene_duration) in enumerate(zip(chosen, scene_durations)):
        clip_duration = scene_duration + (transition if index < len(chosen)-1 else 0)
        frames = max(2, round(clip_duration * 30))
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{clip_duration:.6f}",
                   "-i", item["local_path"]]
        # Keep the crop centered and use a very slow, monotonic zoom.
        # Avoid frame-to-frame horizontal drift, which can look like image shake.
        filters.append(
            f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,zoompan=z='min(1+0.00012*on,1.035)':"
            f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
            f"d={frames}:s=1080x1920:fps=30,format=yuv420p[p{index}]")
    current, elapsed = "p0", scene_durations[0]
    for index in range(1, len(chosen)):
        label = f"x{index}"
        filters.append(
            f"[{current}][p{index}]xfade=transition=fade:duration={transition:.6f}:"
            f"offset={elapsed:.6f}[{label}]")
        current = label
        elapsed += scene_durations[index]
    filters.append(f"[{current}]trim=duration={duration:.6f},setpts=PTS-STARTPTS,format=yuv420p[outv]")
    run(["ffmpeg", "-hide_banner", "-y", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[outv]", "-an", "-t", f"{duration:.6f}", "-c:v", "libx264",
         "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
         str(destination)])
    actual = probe_media_duration(destination)
    if actual + 0.10 < duration:
        raise SystemExit(f"Photo scene reel is too short ({actual:.3f}s for {duration:.3f}s).")
    ids = [item["id"] for item in chosen]
    print("Verse-matched photo backgrounds:", ", ".join(ids))
    return ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default="output/review.mp4")
    parser.add_argument("--background-rotation", action="store_true", help="Select from the approved background catalog.")
    parser.add_argument("--use-photo-backgrounds", action="store_true", help="Use the downloaded Pexels photo library with gentle motion and crossfades.")
    parser.add_argument("--background-rotation-key", default="manual-review")
    parser.add_argument("--recent-background-id", action="append", default=[])
    args = parser.parse_args()
    if args.use_photo_backgrounds and not args.background_rotation_key.strip():
        args.background_rotation_key = secrets.token_hex(16)

    manifest_path = Path(args.manifest)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    background_sequence = None
    if args.background_rotation:
        from background_rotation import order_backgrounds
        background_sequence = order_backgrounds(
            Path("data/background_candidates.json"),
            args.background_rotation_key,
            args.recent_background_id,
        )
        selected_background = dict(background_sequence[0])
        background_sequence = [dict(item) for item in background_sequence]
        selected_background["source_url"] = selected_background["source_page_url"]
        data["visual"]["background_candidate"] = selected_background
        data["visual"].pop("approved_background_url", None)
    # Validate the effective manifest after rotation has selected its approved background.
    validate_content_manifest(data)
    if data.get("content_type", "quran") != "quran":
        raise SystemExit("This renderer currently renders Quran manifests only; dua/dhikr rendering is being added separately.")
    source, audio, visual = data["source"], data["audio"], data["visual"]
    caption = data.get("caption", {})

    # Template selection is manifest-driven. Keep the approved design as the
    # only enabled template until another design is separately reviewed.
    template = visual.get("template", "ornate_gold_classic")
    supported_templates = {"ornate_gold_classic", "nature_clean", "minimal_mushaf", "cinematic_landscape"}
    if template not in supported_templates:
        raise SystemExit(
            f"Unsupported/unapproved visual template: {template}. "
            "Only ornate_gold_classic is currently approved."
        )

    background_url = visual.get("approved_background_url") or visual.get("background_candidate", {}).get("direct_video_url")
    if not background_url:
        raise SystemExit("Manifest must provide an approved background candidate URL.")
    validate_quran_audio_approval(audio)
    background = visual.get("background_candidate", {})
    if not background.get("approved", False):
        raise SystemExit("Background is not marked approved. Refusing to render.")
    if not background.get("user_approved", False):
        raise SystemExit("Background has not been explicitly user-approved. Refusing to render.")
    if data.get("publishing", {}).get("auto_publish", False):
        raise SystemExit("Auto-publishing must remain disabled; renderer is review-only.")

    verses = data.get("verses", [])
    if not verses:
        raise SystemExit("Manifest has no verified verse text.")
    verse_numbers = [int(v["number"]) for v in verses]
    if len(set(verse_numbers)) != len(verse_numbers) or verse_numbers != sorted(verse_numbers):
        raise SystemExit("Verse numbers must be unique and in ascending Quran order.")
    # Do not normalize Unicode, remove harakat, or rewrite Arabic characters.
    for verse in verses:
        if not isinstance(verse.get("arabic"), str) or not verse["arabic"]:
            raise SystemExit("Every verse must contain exact Arabic source text.")
        if not verse.get("english"):
            raise SystemExit("Every verse must contain its paired English translation.")

    # Keep the on-screen title to Arabic letters only; verse range is in caption metadata.
    title = f"سورة {source['surah_name_ar']}"

    work = Path("build")
    work.mkdir(exist_ok=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    audio_file = Path(audio["production_audio_file"])
    bg_file = work / "background.mp4"
    if not audio_file.is_file():
        raise SystemExit(f"Approved audio file missing: {audio_file}")
    scenes = [{"scene": i, "verses": [n]} for i, n in enumerate(verse_numbers, 1)]
    if [n for scene in scenes for n in scene.get("verses", [])] != verse_numbers:
        raise SystemExit("Scene plan must cover every verse exactly once and in order.")
    scene_overlays = []
    for scene in scenes:
        selected = [v for v in verses if int(v["number"]) in scene["verses"]]
        if not selected or [int(v["number"]) for v in selected] != scene["verses"]:
            raise SystemExit("Scene verse selection is invalid or out of order.")
        arabic_overlay = work / f"arabic_scene_{scene['scene']}.png"
        english_overlay = work / f"english_scene_{scene['scene']}.png"
        create_arabic_overlay(title, selected, arabic_overlay, template)
        create_english_overlay(selected, english_overlay)
        scene_overlays.append((scene, arabic_overlay, english_overlay))

    verse_durations = {int(k): float(v) for k, v in audio.get("processed_verse_durations_seconds", {}).items()}
    if set(verse_durations) != set(verse_numbers):
        raise SystemExit("Processed verse timing data is incomplete.")
    inter_verse_gap = float(audio.get("inter_verse_silence_seconds", 0.05))
    # The background reel is built after the exact audio duration is known.

    # Scene boundaries use the approved processed verse durations.
    scene_boundaries = []
    elapsed = 0.0
    for scene in scenes[:-1]:
        elapsed += sum(verse_durations[n] for n in scene["verses"]) + inter_verse_gap * len(scene["verses"])
        scene_boundaries.append(elapsed)

    duration_result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(audio_file)
    ], text=True).strip()
    duration = float(duration_result)
    validate_video_duration(duration)
    if args.use_photo_backgrounds:
        photo_data = json.loads(Path("data/background_photos_manifest.json").read_text(encoding="utf-8"))
        timed_scenes = []
        for index, scene in enumerate(scenes):
            selected_verses = [v for v in verses if int(v["number"]) in scene["verses"]]
            scene_duration = sum(verse_durations[n] for n in scene["verses"])
            if index < len(scenes) - 1:
                scene_duration += inter_verse_gap * len(scene["verses"])
            timed_scenes.append({"verses": selected_verses, "duration": scene_duration})
        build_photo_background_reel(
            photo_data.get("candidates", []), timed_scenes, duration, work, bg_file,
            args.background_rotation_key
        )
    else:
        build_background_reel(
            background_sequence or [background], duration, work, bg_file
        )

    inputs = ["-i", str(bg_file), "-i", str(audio_file)]
    filters = [
        "[0:v]tpad=stop_mode=clone:stop_duration=1,scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,fps=30[vbase]"
    ]
    current = "vbase"
    input_index = 2
    for index, (scene, arabic_overlay, english_overlay) in enumerate(scene_overlays):
        start = 0.0 if index == 0 else scene_boundaries[index - 1]
        end = duration if index == len(scene_overlays) - 1 else scene_boundaries[index]
        scene_length = max(0.05, end - start)
        inputs += [
            "-loop", "1", "-framerate", "30", "-t", f"{scene_length:.6f}",
            "-i", str(arabic_overlay),
            "-loop", "1", "-framerate", "30", "-t", f"{scene_length:.6f}",
            "-i", str(english_overlay),
        ]
        fade_in = 0.28 if index > 0 else 0.45
        fade_out = 0.28 if index < len(scene_overlays) - 1 else 0.0
        arabic_fade = (
            f"[{input_index}:v]format=rgba,fade=t=in:st=0:d={fade_in:.3f}:alpha=1"
        )
        if fade_out:
            arabic_fade += f",fade=t=out:st={max(0.0, scene_length-fade_out):.6f}:d={fade_out:.3f}:alpha=1"
        arabic_fade += f"[ar{index}]"
        filters.append(arabic_fade)
        english_fade = (
            f"[{input_index + 1}:v]format=rgba,fade=t=in:st=0:d={fade_in:.3f}:alpha=1"
        )
        if fade_out:
            english_fade += f",fade=t=out:st={max(0.0, scene_length-fade_out):.6f}:d={fade_out:.3f}:alpha=1"
        english_fade += f"[en{index}]"
        filters.append(english_fade)
        filters.append(
            f"[{current}][ar{index}]overlay=0:0:enable='between(t,{start:.6f},{end:.6f})'[v{index}a]"
        )
        filters.append(
            f"[v{index}a][en{index}]overlay=0:0:enable='between(t,{start:.6f},{end:.6f})'[v{index}]"
        )
        current = f"v{index}"
        input_index += 2
    draw = ";".join(filters)
    run([
        "ffmpeg", "-hide_banner", "-y", *inputs, "-filter_complex", draw,
        "-map", f"[{current}]", "-map", "1:a", "-t", str(duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-map_metadata", "-1", "-map_chapters", "-1",
        "-movflags", "+faststart", str(output)
    ])

    caption_path = output.with_suffix(".caption.json")
    hashtag_sets = build_hashtags(str(data.get("id", "")), caption)
    caption_path.write_text(json.dumps({
        "status": "review_required",
        "surah": source["surah_name_ar"],
        "verses": verse_numbers,
        "arabic_caption": caption.get("arabic", ""),
        "english_caption": caption.get("english", ""),
        "hashtags_ar": hashtag_sets["ar"],
        "hashtags_en": hashtag_sets["en"],
        "hashtags_fr": hashtag_sets["fr"],
        "hashtags_tr": hashtag_sets["tr"],
        "hashtags_id": hashtag_sets["id"],
        "reciter_public_attribution": False,
        "publishing": "disabled"
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rendered review video: {output} ({duration:.2f}s)")
    print(f"Caption for review: {caption_path}")


if __name__ == "__main__":
    main()
