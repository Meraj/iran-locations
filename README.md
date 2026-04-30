# locations-data

A list of Iran locations, kept in this repo as JSON and refreshed via a small Python CLI.

Today the dataset covers the 31 Iranian provinces (`data/provinces.json`), sourced from the GNAF tables behind <https://gnaf2.post.ir/proposal>. More layers (cities, districts, villages) will be added next to it.

## How it works

The CLI calls the GNAF OData endpoint and writes the response to `data/provinces.json`. The endpoint requires an `x-api-key` request header, which you grab from the proposal page in your browser; it isn't stored in the repo.

## Refresh `data/provinces.json`

1. Open <https://gnaf2.post.ir/proposal>.
2. Open DevTools → Network, trigger any request, and copy the `x-api-key` header from a request to `gnaf2.post.ir`.
3. Run:

   ```sh
   uv run python main.py fetch-provinces --x-api-key <X_API_KEY>
   ```

That overwrites `data/provinces.json` (currently 31 rows). The CLI help (`--help`) repeats these steps.

## Layout

- `main.py` — Typer CLI entry point.
- `provinces.py` — fetch/save logic for provinces; extend here when adding more location layers.
- `data/provinces.json` — committed dataset (OData shape: `{ "odata.count": N, "value": [...] }`).

## Requirements

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) for dependency management
