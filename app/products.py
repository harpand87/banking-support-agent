import json
from pathlib import Path
from typing import Any


DEFAULT_RATES_FILE = Path(__file__).resolve().parents[1] / "data" / "products" / "synthetic_deposit_rates.json"


def load_deposit_rates(path: str | Path = DEFAULT_RATES_FILE) -> dict[str, Any]:
    """Load explicitly synthetic FD/RD example rates after schema validation."""
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("unsupported deposit-rate schema")
    if data.get("status") != "synthetic_example_only":
        raise ValueError("only synthetic example rates can be loaded")
    if not isinstance(data.get("disclaimer"), str) or not data["disclaimer"].strip():
        raise ValueError("deposit-rate data must include a disclaimer")
    rates = data.get("rates")
    if not isinstance(rates, dict) or set(rates) != {"FD", "RD"}:
        raise ValueError("deposit-rate data must include FD and RD values")
    for product, entry in rates.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("annual_rate_percent"), (int, float)):
            raise ValueError(f"invalid {product} rate entry")
        if not 0 <= entry["annual_rate_percent"] <= 100:
            raise ValueError(f"{product} annual rate is outside the allowed range")
        if not isinstance(entry.get("source"), str) or not entry["source"].startswith("KB-"):
            raise ValueError(f"{product} rate must cite a knowledge source")
    return data
