#!/usr/bin/env python3
"""Fetch the app's Google Fonts and emit a self-contained @font-face CSS
with the woff2 payloads inlined as data URIs (make-pdf renders offline)."""
import base64
import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
CSS_URL = ("https://fonts.googleapis.com/css2?"
           "family=Cinzel:wght@400;700;900&"
           "family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&"
           "display=swap")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read()


css = get(CSS_URL).decode("utf-8")
blocks = re.findall(r"@font-face\s*\{[^}]*\}", css)

out, kept = [], 0
for block in blocks:
    rng = re.search(r"unicode-range:\s*([^;]+);", block)
    # Latin + Latin-Ext only: German umlauts live in U+0000-00FF, and
    # dropping cyrillic/greek/vietnamese keeps the payload small.
    if rng and "U+0000-00FF" not in rng.group(1) and "U+0100-02BA" not in rng.group(1):
        continue
    m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
    if not m:
        continue
    b64 = base64.b64encode(get(m.group(1))).decode("ascii")
    out.append(block.replace(m.group(1), f"data:font/woff2;base64,{b64}"))
    kept += 1

if kept == 0:
    sys.exit("no font faces matched — aborting rather than emitting empty CSS")

path = sys.argv[1]
with open(path, "w") as fh:
    fh.write("\n".join(out))

names = sorted(set(re.findall(r"font-family:\s*'([^']+)'", "\n".join(out))))
size_kb = len("\n".join(out).encode()) / 1024
print(f"{kept} faces, {', '.join(names)}, {size_kb:.0f}KB → {path}")
