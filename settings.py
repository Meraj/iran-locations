import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

OVERPASS_API = "https://overpass-api.de/api/interpreter"
USER_AGENT = "locations-data/0.1"


def log(message: str) -> None:
    """Write a progress line to stderr."""
    print(message, file=sys.stderr, flush=True)


@contextmanager
def heartbeat(message: str, *, interval: float = 15.0):
    """Print `message` with elapsed seconds every `interval` until exit."""
    stop = threading.Event()
    started = time.monotonic()

    def _run():
        while not stop.wait(interval):
            log(f"  ...{message} (elapsed {time.monotonic() - started:.0f}s)")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join(timeout=1.0)
