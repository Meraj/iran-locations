import json

import httpx

from settings import DATA_DIR, OVERPASS_API, USER_AGENT

CITIES_FILE = DATA_DIR / "cities.json"


def _query(relation_id: int) -> str:
    return f"""\
[out:json][timeout:180];
relation({relation_id})->.p;
.p map_to_area->.a;
node(area.a)["place"~"^(city|town)$"];
out tags;
"""


def fetch_cities(provinces: list[dict], timeout: float = 300.0) -> dict:
    """Fetch place=city|town nodes for each province relation."""
    out: dict[str, dict] = {}
    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        for p in provinces:
            if p.get("type") != "relation":
                continue
            rid = p["id"]
            resp = client.post(OVERPASS_API, data={"data": _query(rid)})
            resp.raise_for_status()
            out[str(rid)] = {
                "name": (p.get("tags") or {}).get("name"),
                "cities": resp.json().get("elements", []),
            }
    return out


def save_cities(payload: dict) -> int:
    CITIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CITIES_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return sum(len(p["cities"]) for p in payload.values())
