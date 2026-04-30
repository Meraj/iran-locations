import httpx
import typer

from cities_osm import CITIES_OSM_FILE, fetch_cities_osm, save_cities_osm
from neighborhoods_osm import (
    NEIGHBORHOODS_OSM_FILE,
    build_neighborhoods_osm,
    fetch_neighborhoods_osm_by_city,
    fetch_neighborhoods_osm_by_province,
    save_neighborhoods_osm_run,
)
from provinces import PROVINCES_FILE, fetch_provinces, save_provinces
from provinces_osm import (
    PROVINCES_OSM_FILE,
    fetch_provinces_osm,
    save_provinces_osm,
)

PROVINCES_GUIDE = """\
How to fetch Iran provinces:

\b
  1. Open https://gnaf2.post.ir/proposal in your browser.
  2. Open DevTools -> Network, trigger any request, and copy
     the `x-api-key` request header from a request to
     gnaf2.post.ir.
  3. Run: locations fetch-provinces --x-api-key <X_API_KEY>
  4. The result is written to data/provinces.json
     (committed to the repo).
"""

app = typer.Typer(
    help=f"Iran Locations data CLI.\n\n{PROVINCES_GUIDE}",
    no_args_is_help=True,
    rich_markup_mode=None,
)


@app.command(name="fetch-provinces", help=PROVINCES_GUIDE)
def fetch_provinces_cmd(
    x_api_key: str = typer.Option(..., "--x-api-key", help="Value of the `x-api-key` request header on gnaf2.post.ir."),
    top: int = typer.Option(200, "--top", help="OData $top page size."),
) -> None:
    """Fetch all 31 Iran provinces from gnaf2.post.ir and overwrite data/provinces.json."""
    try:
        payload = fetch_provinces(x_api_key, top=top)
    except httpx.HTTPStatusError as e:
        typer.echo(
            f"Request failed: {e.response.status_code} {e.response.reason_phrase}\n{e.response.text}",
            err=True,
        )
        raise typer.Exit(1)
    except httpx.RequestError as e:
        typer.echo(f"Network error: {e}", err=True)
        raise typer.Exit(1)

    count = save_provinces(payload)
    typer.echo(f"Saved {count} provinces to {PROVINCES_FILE}")


@app.command(name="fetch-provinces-osm")
def fetch_provinces_osm_cmd() -> None:
    """Fetch all Iran provinces from OSM Overpass and overwrite data/provinces_osm.json."""
    payload = fetch_provinces_osm()
    count = save_provinces_osm(payload)
    typer.echo(f"Saved {count} provinces to {PROVINCES_OSM_FILE}")


@app.command(name="fetch-cities-osm")
def fetch_cities_osm_cmd() -> None:
    """Fetch place=city|town for each province from OSM Overpass and overwrite data/cities_osm.json."""
    payload = fetch_cities_osm()
    total = save_cities_osm(payload)
    typer.echo(f"Saved {total} cities across {len(payload)} provinces to {CITIES_OSM_FILE}")


@app.command(name="fetch-neighborhoods-osm")
def fetch_neighborhoods_osm_cmd(
    province: int | None = typer.Option(None, "--province", help="Province (admin_level=4) relation id to scope to."),
    city: int | None = typer.Option(None, "--city", help="City (admin_level=8) relation id to scope to."),
) -> None:
    """Fetch admin_level=8 cities (with boundary) and their neighborhood features (with boundary where present) from OSM Overpass.

    Provide exactly one of --province or --city. Results merge into data/neighborhoods_osm.json.
    """
    if (province is None) == (city is None):
        typer.echo("Provide exactly one of --province or --city.", err=True)
        raise typer.Exit(2)

    if province is not None:
        payload = fetch_neighborhoods_osm_by_province(province)
        path, total = save_neighborhoods_osm_run(payload, scope="province", scope_id=province)
    else:
        payload = fetch_neighborhoods_osm_by_city(city)  # type: ignore[arg-type]
        path, total = save_neighborhoods_osm_run(payload, scope="city", scope_id=city)  # type: ignore[arg-type]

    typer.echo(f"Fetched {total} neighborhoods across {len(payload)} cities. Saved to {path}")


@app.command(name="build-neighborhoods-osm")
def build_neighborhoods_osm_cmd() -> None:
    """Merge all per-run files under data/neighborhoods_osm/ into data/neighborhoods_osm.json."""
    cities, total = build_neighborhoods_osm()
    typer.echo(f"Merged {cities} cities ({total} neighborhoods) into {NEIGHBORHOODS_OSM_FILE}")


@app.command()
def version() -> None:
    typer.echo("iran-locations-data 0.1.0")


if __name__ == "__main__":
    app()
