"""Fetch + pre-process the real thumbnail and channel avatar for the youtube_card
mock, into committed PNGs beside this file (<key>_thumb.png, <key>_avatar.png).

The images are PRE-MASKED so manim's ImageMobject shows them directly: the thumbnail
gets rounded corners and the avatar is circle-cropped (transparent PNGs). Run with the
RENDER venv (it ships Pillow):

    <video>/.venv/bin/python animations/assets/youtube_media/fetch.py

Both URLs come from the YouTube Data API (`videos.list` → the video's thumbnail +
channelId, `channels.list` → the channel avatar), authenticated with the
`YOUTUBE_API_KEY` in `analytics/.env`. Refresh rarely — a thumbnail/avatar changes
seldom. Keep the id list in step with youtube_data.VIDEOS.
"""
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

OUT = Path(__file__).resolve().parent
_ENV = Path(__file__).resolve().parents[4] / "analytics" / ".env"
VIDEOS = {"hangman": "le5uGqHKll8"}   # scene key -> YouTube video id


def _api_key():
    for line in _ENV.read_text().splitlines():
        k, _, v = line.partition("=")
        if k.strip() == "YOUTUBE_API_KEY":
            return v.strip().strip('"').strip("'")
    raise RuntimeError(f"YOUTUBE_API_KEY not found in {_ENV}")


_KEY = _api_key()


def _api(endpoint, **params):
    params["key"] = _KEY
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as r:
        return json.load(r)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def _best(thumbnails):
    for size in ("maxres", "standard", "high", "medium", "default"):
        if size in thumbnails:
            return thumbnails[size]["url"]
    raise RuntimeError("no thumbnail sizes returned")


def _open(data):
    return Image.open(io.BytesIO(data)).convert("RGBA")


def _rounded(img, frac=0.045):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=int(min(w, h) * frac), fill=255)
    img.putalpha(mask)
    return img


def _circle(img):
    img = ImageOps.fit(img, (min(img.size),) * 2)     # center-crop to square
    s = img.size[0]
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, s - 1, s - 1], fill=255)
    img.putalpha(mask)
    return img


if __name__ == "__main__":
    for key, vid in VIDEOS.items():
        v = _api("videos", part="snippet", id=vid)["items"][0]["snippet"]
        chan = _api("channels", part="snippet", id=v["channelId"])["items"][0]["snippet"]

        thumb = _rounded(_open(_get(_best(v["thumbnails"]))))
        thumb.save(OUT / f"{key}_thumb.png")
        avatar = _circle(_open(_get(_best(chan["thumbnails"]))))
        avatar.save(OUT / f"{key}_avatar.png")
        print(f"{key}: {key}_thumb.png {thumb.size}, {key}_avatar.png {avatar.size}")
