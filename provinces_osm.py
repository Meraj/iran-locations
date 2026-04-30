import json
import time

import httpx

from settings import DATA_DIR, OVERPASS_API, USER_AGENT, heartbeat, log

PROVINCES_OSM_FILE = DATA_DIR / "provinces_osm.json"

QUERY = """\
[out:json][timeout:180];
area["ISO3166-1"="IR"][admin_level=2]->.iran;
relation(area.iran)["admin_level"="4"]["boundary"="administrative"];
out tags;
"""


def fetch_provinces_osm(timeout: float = 300.0) -> dict:
    log(f"[provinces-osm] POST {OVERPASS_API} (timeout={timeout:.0f}s)")
    started = time.monotonic()
    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        with heartbeat("[provinces-osm] waiting for Overpass"):
            resp = client.post(OVERPASS_API, data={"data": QUERY})
    log(
        f"[provinces-osm] {resp.status_code} {resp.reason_phrase} in "
        f"{time.monotonic() - started:.1f}s ({len(resp.content):,} bytes)"
    )
    resp.raise_for_status()
    data = resp.json()
    log(f"[provinces-osm] got {len(data.get('elements', [])):,} elements")
    return data


def save_provinces_osm(payload: dict) -> int:
    PROVINCES_OSM_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROVINCES_OSM_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(payload.get("elements", []))
