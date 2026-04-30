import httpx
import typer

from provinces import PROVINCES_FILE, fetch_provinces, save_provinces

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


@app.command()
def version() -> None:
    typer.echo("iran-locations-data 0.1.0")


if __name__ == "__main__":
    app()
