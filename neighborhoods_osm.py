import json

import httpx

from settings import DATA_DIR, OVERPASS_API, USER_AGENT

NEIGHBORHOODS_OSM_FILE = DATA_DIR / "neighborhoods_osm.json"

# One Overpass call: foreach admin_level=8 city in Iran, emit the relation
# tags then the neighborhood-level features inside its area
# (place=neighbourhood|suburb|quarter nodes and admin_level=9|10 relations).
# Output is parsed sequentially: each `relation` element with admin_level=8
# starts a new city bucket, subsequent elements belong to it until the next
# admin_level=8 relation.
QUERY = """\
[out:json][timeout:900];
area["ISO3166-1"="IR"][admin_level=2]->.iran;
rel(area.iran)["admin_level"="8"]["boundary"="administrative"]->.cities;
foreach .cities->.c (
  .c out tags;
  .c map_to_area->.carea;
  (
    node(area.carea)["place"~"^(neighbourhood|suburb|quarter)$"];
    rel(area.carea)["admin_level"~"^(9|10)$"]["boundary"="administrative"];
  );
  out tags;
);
"""


def fetch_neighborhoods_osm(timeout: float = 900.0) -> dict:
    """Fetch neighborhood-level features grouped by admin_level=8 city via a single Overpass call."""
    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.post(OVERPASS_API, data={"data": QUERY})
        resp.raise_for_status()
        data = resp.json()

    out: dict[str, dict] = {}
    current: dict | None = None
    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        if el.get("type") == "relation" and tags.get("admin_level") == "8":
            current = {
                "name": tags.get("name"),
                "neighborhoods": [],
            }
            out[str(el["id"])] = current
        elif current is not None:
            current["neighborhoods"].append(el)
    return out


def save_neighborhoods_osm(payload: dict) -> int:
    NEIGHBORHOODS_OSM_FILE.parent.mkdir(parents=True, exist_ok=True)
    NEIGHBORHOODS_OSM_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sum(len(c["neighborhoods"]) for c in payload.values())
