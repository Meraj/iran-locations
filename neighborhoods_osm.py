import json

import httpx

from settings import DATA_DIR, OVERPASS_API, USER_AGENT

NEIGHBORHOODS_OSM_FILE = DATA_DIR / "neighborhoods_osm.json"

# Per-province query: foreach admin_level=8 city in the given province,
# emit the city relation (with geometry) then the neighborhood-level
# features inside its area (with geometry).
QUERY_PROVINCE = """\
[out:json][timeout:600];
rel({province_id})->.province;
.province map_to_area->.parea;
rel(area.parea)["admin_level"="8"]["boundary"="administrative"]->.cities;
foreach .cities->.c (
  .c out geom;
  .c map_to_area->.carea;
  (
    node(area.carea)["place"~"^(neighbourhood|suburb|quarter)$"];
    rel(area.carea)["admin_level"~"^(9|10)$"]["boundary"="administrative"];
  );
  out geom;
);
"""

# Per-city query: emit one admin_level=8 city (with geometry) and the
# neighborhood-level features inside it (with geometry).
QUERY_CITY = """\
[out:json][timeout:300];
rel({city_id})->.c;
.c out geom;
.c map_to_area->.carea;
(
  node(area.carea)["place"~"^(neighbourhood|suburb|quarter)$"];
  rel(area.carea)["admin_level"~"^(9|10)$"]["boundary"="administrative"];
);
out geom;
"""


def fetch_neighborhoods_osm_by_province(province_id: int, timeout: float = 700.0) -> dict:
    return _fetch(QUERY_PROVINCE.format(province_id=province_id), timeout)


def fetch_neighborhoods_osm_by_city(city_id: int, timeout: float = 300.0) -> dict:
    return _fetch(QUERY_CITY.format(city_id=city_id), timeout)


def _fetch(query: str, timeout: float) -> dict:
    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.post(OVERPASS_API, data={"data": query})
        resp.raise_for_status()
        data = resp.json()

    out: dict[str, dict] = {}
    current: dict | None = None
    for el in data.get("elements", []):
        tags = el.get("tags") or {}
        if el.get("type") == "relation" and tags.get("admin_level") == "8":
            current = {
                "city": el,
                "neighborhoods": [],
            }
            out[str(el["id"])] = current
        elif current is not None:
            current["neighborhoods"].append(el)
    return out


def save_neighborhoods_osm(payload: dict) -> int:
    """Merge payload into data/neighborhoods_osm.json. Returns neighborhood count for this payload."""
    existing: dict = {}
    if NEIGHBORHOODS_OSM_FILE.exists():
        existing = json.loads(NEIGHBORHOODS_OSM_FILE.read_text(encoding="utf-8"))
    existing.update(payload)
    NEIGHBORHOODS_OSM_FILE.parent.mkdir(parents=True, exist_ok=True)
    NEIGHBORHOODS_OSM_FILE.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sum(len(c["neighborhoods"]) for c in payload.values())
