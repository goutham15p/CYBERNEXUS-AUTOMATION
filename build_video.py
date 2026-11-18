
import os
import requests
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

API_KEY = os.environ["PEXELS_API_KEY"]
OUT = Path("output")
ASSETS = Path("assets")
OUT.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)

SCENES = [
    ("THE DIGITAL SHADOW", "A hidden world exists behind every connected screen.", "cybersecurity computer dark"),
    ("A WORLD OF HACKERS", "Not every hacker has the same intentions.", "computer coding dark room"),
    ("WHAT IS A HACKER?", "A hacker explores systems, weaknesses and technology.", "programmer computer code"),
    ("BLACK HAT HACKERS", "Some exploit vulnerabilities for criminal purposes.", "dark computer hacker"),
    ("WHITE HAT HACKERS", "Ethical hackers test systems with permission.", "cybersecurity professional"),
    ("GREY HAT HACKERS", "Intent and authorization make an important difference.", "network security computer"),
    ("HOW ATTACKS BEGIN", "Many attacks begin with information gathering.", "server network data center"),
    ("DEFENDING THE DIGITAL WORLD", "Security teams investigate, protect and respond.", "cybersecurity monitoring")
]

def get_clip(query, index):
    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": API_KEY},
        params={"query": query, "per_page": 10, "orientation": "landscape"},
        timeout=60
    )
    response.raise_for_status()
    videos = response.json().get("videos", [])
    if not videos:
        raise RuntimeError("No Pexels videos found for: " + query)

    files = videos[0].get("video_files", [])
    files = [f for f in files if f.get("link")]
    files.sort(key=lambda f: f.get("width", 0), reverse=True)
    link = files[0]["link"]

    path = ASSETS / f"scene_{index}.mp4"
    with requests.get(link, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, "wb") as output:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    output.write(chunk)
    return path

def make_overlay(title, description, index):
    image = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 78
    )
    font_body = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42
    )
    draw.rectangle((0, 730, 1920, 1080), fill=(2, 10, 25, 205))
    draw.text((100, 790), title, font=font_title, fill=(0, 220, 255, 255))
    draw.text((100, 910), description, font=font_body, fill="white")
    draw.text((100, 1010), "CYBERNEXUS  |  EXPLORE. ANALYZE. DEFEND.",
              font=font_body, fill=(180, 205, 220, 255))
    path = ASSETS / f"overlay_{index}.png"
    image.save(path)
    return path

segments = []

for i, (title, description, query) in enumerate(SCENES):
    print("Creating scene:", title)
    clip = get_clip(query, i)
    overlay = make_overlay(title, description, i)
    segment = OUT / f"segment_{i}.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(clip),
        "-loop", "1", "-i", str(overlay),
        "-t", "60",
        "-filter_complex",
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,setsar=1[bg];"
        "[bg][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "25", "-r", "24",
        str(segment)
    ], check=True)
    segments.append(segment)

concat_file = OUT / "concat.txt"
concat_file.write_text(
    "".join(f"file '{p.resolve()}'\n" for p in segments)
)

subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_file), "-c", "copy",
    str(OUT / "cybernexus_episode01.mp4")
], check=True)

print("Video created:", OUT / "cybernexus_episode01.mp4")
