import logging
from datetime import datetime, timezone

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
