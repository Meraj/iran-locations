import json
import ssl

import httpx

from settings import DATA_DIR

PROVINCES_FILE = DATA_DIR / "provinces.json"

PROVINCE_API = "https://gnaf2.post.ir/sina/editor/tables/province/rows"
REFERER = "https://gnaf2.post.ir/proposal"


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # gnaf2.post.ir negotiates legacy ciphers; mirrors Node's DEFAULT@SECLEVEL=0.
    ctx.set_ciphers("DEFAULT@SECLEVEL=0")
    return ctx


def _headers(x_api_key: str) -> dict[str, str]:
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,fa;q=0.8",
        "content-type": "application/json",
        "x-api-key": x_api_key,
        "Referer": REFERER,
    }


def fetch_provinces(x_api_key: str, top: int = 200) -> dict:
    """Fetch the OData payload of Iran provinces from gnaf2.post.ir."""
    with httpx.Client(verify=_ssl_context(), timeout=30.0) as client:
        resp = client.get(
            PROVINCE_API,
            params={"$top": top, "$orderby": "name"},
            headers=_headers(x_api_key),
        )
        resp.raise_for_status()
        return resp.json()


def save_provinces(payload: dict) -> int:
    """Write the OData payload to data/provinces.json. Returns the row count."""
    PROVINCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROVINCES_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if isinstance(payload, dict):
        return len(payload.get("value", []))
    return len(payload)
