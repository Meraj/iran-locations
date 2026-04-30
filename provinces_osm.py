import json

import httpx

from settings import DATA_DIR, OVERPASS_API, USER_AGENT

PROVINCES_OSM_FILE = DATA_DIR / "provinces_osm.json"

QUERY = """\
[out:json][timeout:180];
area["ISO3166-1"="IR"][admin_level=2]->.iran;
relation(area.iran)["admin_level"="4"]["boundary"="administrative"];
out tags;
"""


def fetch_provinces_osm(timeout: float = 300.0) -> dict:
    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.post(OVERPASS_API, data={"data": QUERY})
        resp.raise_for_status()
        return resp.json()


def save_provinces_osm(payload: dict) -> int:
    PROVINCES_OSM_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROVINCES_OSM_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(payload.get("elements", []))
