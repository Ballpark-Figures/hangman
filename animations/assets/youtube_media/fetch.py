"""Fetch + pre-process the real thumbnail and channel avatar for the youtube_card
mock, into committed PNGs beside this file (<key>_thumb.png, <key>_avatar.png).

The images are PRE-MASKED so manim's ImageMobject shows them directly: the thumbnail
gets rounded corners and the avatar is circle-cropped (transparent PNGs). Run with the
RENDER venv (it ships Pillow):

    <video>/.venv/bin/python animations/assets/youtube_media/fetch.py

Sources: the thumbnail is the public CDN still (i.ytimg.com — no API); the avatar is
the channel page's og:image (the local analytics `.env` has no usable Data-API key).
Refresh rarely — a thumbnail/avatar changes seldom. Keep the id/handle list in step
with youtube_data.VIDEOS.
"""
import io
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

OUT = Path(__file__).resolve().parent
# scene key -> (YouTube video id, channel @handle)
VIDEOS = {"hangman": ("le5uGqHKll8", "@hbmmaster")}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def _avatar_url(handle):
    html = _get(f"https://www.youtube.com/{handle}").decode("utf-8", "ignore")
    m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if not m:
        raise RuntimeError(f"no og:image (avatar) found for {handle}")
    return m.group(1)


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


def _open(data):
    return Image.open(io.BytesIO(data)).convert("RGBA")


if __name__ == "__main__":
    for key, (vid, handle) in VIDEOS.items():
        thumb = _rounded(_open(_get(f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg")))
        thumb.save(OUT / f"{key}_thumb.png")
        avatar = _circle(_open(_get(_avatar_url(handle))))
        avatar.save(OUT / f"{key}_avatar.png")
        print(f"{key}: {key}_thumb.png {thumb.size}, {key}_avatar.png {avatar.size}")
