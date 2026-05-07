"""
Download ~100 public-domain classical artworks from the Met Museum API.
Saves images to uncanny_maker/catalog/  (created automatically).

Usage:
    python download_catalog.py

No API key required. Images are public domain.
"""

import os
import time
import pathlib
import requests

CATALOG_DIR = pathlib.Path(__file__).parent / "catalog"
API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
TARGET = 100
REQUEST_DELAY = 0.25  # seconds between requests — be polite to the API

# Search terms and the Met department IDs they map to.
# Department IDs: 13 = Greek & Roman, 11 = European Paintings, 17 = Medieval Art,
# 6 = Asian Art (classical sculpture), 14 = Islamic Art
SEARCHES = [
    {"q": "portrait",           "departmentIds": 11},  # European oil portraits
    {"q": "marble statue",      "departmentIds": 13},  # Greek & Roman sculpture
    {"q": "bust",               "departmentIds": 13},  # Roman portrait busts
    {"q": "venus",              "departmentIds": 13},  # Venus statues
    {"q": "apollo",             "departmentIds": 13},  # Apollo statues
    {"q": "madonna",            "departmentIds": 11},  # Renaissance Madonnas
    {"q": "mythological",       "departmentIds": 11},  # Baroque mythological scenes
    {"q": "portrait",           "departmentIds": 17},  # Medieval portraits
    {"q": "emperor",            "departmentIds": 13},  # Roman emperor busts
    {"q": "goddess",            "departmentIds": 13},  # Goddess figures
]


def search_objects(q: str, department_id: int) -> list[int]:
    params = {
        "hasImages": "true",
        "isPublicDomain": "true",
        "q": q,
        "departmentId": department_id,
    }
    resp = requests.get(f"{API_BASE}/search", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("objectIDs") or []


def fetch_object(object_id: int) -> dict | None:
    resp = requests.get(f"{API_BASE}/objects/{object_id}", timeout=15)
    resp.raise_for_status()
    obj = resp.json()
    url = obj.get("primaryImageSmall") or obj.get("primaryImage")
    if not url:
        return None
    return {
        "id": object_id,
        "title": obj.get("title", "Untitled"),
        "artist": obj.get("artistDisplayName", "Unknown"),
        "date": obj.get("objectDate", ""),
        "department": obj.get("department", ""),
        "url": url,
    }


def safe_filename(title: str, object_id: int) -> str:
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in title)
    slug = slug.strip().replace(" ", "_")[:40]
    return f"{slug}_{object_id}.jpg"


def download_image(url: str, dest: pathlib.Path) -> bool:
    try:
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    ! Download failed: {e}")
        return False


def main():
    CATALOG_DIR.mkdir(exist_ok=True)
    print(f"Saving images to: {CATALOG_DIR}\n")

    seen_ids: set[int] = set()
    candidates: list[dict] = []

    # Gather object IDs across all search queries
    print("Searching Met collection…")
    for search in SEARCHES:
        if len(candidates) >= TARGET * 3:
            break
        ids = search_objects(search["q"], search["departmentIds"])
        new = [i for i in ids if i not in seen_ids]
        seen_ids.update(new)
        print(f"  '{search['q']}' dept={search['departmentIds']}: {len(ids)} results, {len(new)} new")
        # Spread IDs evenly — take every Nth to get variety
        step = max(1, len(new) // 20)
        candidates.extend(new[::step][:20])
        time.sleep(REQUEST_DELAY)

    print(f"\n{len(candidates)} candidate objects. Fetching metadata + downloading images…\n")

    downloaded = 0
    skipped = 0

    for obj_id in candidates:
        if downloaded >= TARGET:
            break

        try:
            meta = fetch_object(obj_id)
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            print(f"  [{obj_id}] metadata error: {e}")
            skipped += 1
            continue

        if meta is None:
            skipped += 1
            continue

        filename = safe_filename(meta["title"], meta["id"])
        dest = CATALOG_DIR / filename

        if dest.exists():
            print(f"  [{downloaded+1:>3}] already exists — {filename}")
            downloaded += 1
            continue

        print(f"  [{downloaded+1:>3}] {meta['title'][:50]} ({meta['artist'][:30]}, {meta['date']})")
        success = download_image(meta["url"], dest)
        if success:
            downloaded += 1
        else:
            skipped += 1

        time.sleep(REQUEST_DELAY)

    print(f"\nDone. {downloaded} images downloaded, {skipped} skipped.")
    print(f"Catalog: {CATALOG_DIR}")


if __name__ == "__main__":
    main()
