import json

import httpx

from settings import DATA_DIR, OVERPASS_API, USER_AGENT

CITIES_OSM_FILE = DATA_DIR / "cities_osm.json"

# One Overpass call: foreach province, emit the relation tags then the
# place=city|town nodes inside its area. Output is parsed sequentially:
# each `relation` element starts a new province bucket, subsequent `node`
# elements belong to it until the next relation.
QUERY = """\
[out:json][timeout:600];
area["ISO3166-1"="IR"][admin_level=2]->.iran;
rel(area.iran)["admin_level"="4"]["boundary"="administrative"]->.provinces;
foreach .provinces->.p (
  .p out tags;
  .p map_to_area->.parea;
  node(area.parea)["place"~"^(city|town)$"];
  out tags;
);
"""


def fetch_cities_osm(timeout: float = 600.0) -> dict:
    """Fetch place=city|town nodes grouped by province via a single Overpass call."""
    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.post(OVERPASS_API, data={"data": QUERY})
        resp.raise_for_status()
        data = resp.json()

    out: dict[str, dict] = {}
    current: dict | None = None
    for el in data.get("elements", []):
        if el.get("type") == "relation":
            current = {
                "name": (el.get("tags") or {}).get("name"),
                "cities": [],
            }
            out[str(el["id"])] = current
        elif el.get("type") == "node" and current is not None:
            current["cities"].append(el)
    return out


def save_cities_osm(payload: dict) -> int:
    CITIES_OSM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CITIES_OSM_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sum(len(p["cities"]) for p in payload.values())
