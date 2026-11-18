
import os
import requests
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PIXABAY_API_KEY: ${{ secrets.PIXABAY_API_KEY }}
if not API_KEY:
    raise RuntimeError("Missing PIXABAY_API_KEY GitHub secret")

OUT = Path("output")
ASSETS = Path("assets")
OUT.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)

SCENES = [
    ("THE DIGITAL SHADOW", "A hidden world exists behind every connected screen.", "cybersecurity"),
    ("A WORLD OF HACKERS", "Not every hacker has the same intentions.", "computer coding"),
    ("WHAT IS A HACKER?", "A hacker explores systems and technology.", "programmer computer"),
    ("BLACK HAT HACKERS", "Some exploit vulnerabilities for criminal purposes.", "dark computer"),
    ("WHITE HAT HACKERS", "Ethical hackers test systems with permission.", "cybersecurity professional"),
    ("GREY HAT HACKERS", "Authorization makes an important difference.", "network security"),
    ("HOW ATTACKS BEGIN", "Many attacks begin with information gathering.", "data center server"),
    ("DEFENDING THE DIGITAL WORLD", "Security teams investigate, protect and respond.", "security monitoring")
]

def download_video(query, index):
    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": API_KEY,
            "q": query,
            "video_type": "film",
            "safesearch": "true",
            "per_page": 10,
            "order": "popular"
        },
        timeout=60
    )
    response.raise_for_status()
    hits = response.json().get("hits", [])

    if not hits:
        raise RuntimeError("No Pixabay video found: " + query)

    video_options = hits[0].get("videos", {})
    video = video_options.get("medium") or video_options.get("small")

    if not video or not video.get("url"):
        raise RuntimeError("No downloadable video file for: " + query)

    path = ASSETS / f"scene_{index}.mp4"

    with requests.get(video["url"], stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

    with open(OUT / "pixabay_sources.txt", "a") as f:
        f.write(f"{query}: {hits[0].get('pageURL', '')}\n")

    return path

def make_overlay(title, description, index):
    image = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    title_font = ImageFont.truetype(bold_path, 48)
    body_font = ImageFont.truetype(font_path, 27)

    draw.rectangle((0, 480, 1280, 720), fill=(2, 10, 25, 220))
    draw.text((65, 515), title, font=title_font, fill=(0, 220, 255, 255))
    draw.text((65, 590), description, font=body_font, fill="white")
    draw.text(
        (65, 660),
        "CYBERNEXUS | EXPLORE. ANALYZE. DEFEND.",
        font=body_font,
        fill=(180, 205, 220, 255)
    )

    path = ASSETS / f"overlay_{index}.png"
    image.save(path)
    return path

segments = []

for i, (title, description, query) in enumerate(SCENES):
    print("Creating:", title)

    clip = download_video(query, i)
    overlay = make_overlay(title, description, i)
    segment = OUT / f"segment_{i}.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(clip),
        "-loop", "1", "-i", str(overlay),
        "-t", "60",
        "-filter_complex",
        "[0:v]scale=1280:720:force_original_aspect_ratio=increase,"
        "crop=1280:720,setsar=1[bg];"
        "[bg][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-crf", "28", "-r", "24",
        str(segment)
    ], check=True)

    segments.append(segment)

concat_file = OUT / "concat.txt"
concat_file.write_text(
    "".join(f"file '{p.resolve()}'\n" for p in segments)
)

final_video = OUT / "cybernexus_episode01.mp4"

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", str(concat_file),
    "-c", "copy",
    str(final_video)
], check=True)

print("SUCCESS:", final_video)

