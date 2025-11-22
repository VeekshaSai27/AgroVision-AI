"""
api_service.py
Utilities to query the data.gov.in mandi prices dataset.

Place this file in the same directory as your `config.py`
(e.g. market_api_using_data_gov/agri_market_app/backend/).
"""

import time
import requests
from urllib.parse import urljoin
from typing import Optional, List, Dict, Any, Union

# Import local config properly
from . import config

# Retry settings
_MAX_RETRIES = 2
_RETRY_BACKOFF = 1.0  # seconds


def _call_api(params: Dict[str, Any]) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    url = urljoin(config.DATA_GOV_BASE + "/", config.RESOURCE_ID)
    headers = {"User-Agent": "Agri-Market-App/1.0"}

    if config.DATA_GOV_API_KEY:
        params["api-key"] = config.DATA_GOV_API_KEY

    last_err = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            return payload.get("records", [])
        except requests.RequestException as e:
            last_err = f"Request error: {e}"
        except ValueError:
            last_err = "Invalid JSON response from data.gov.in"

        if attempt < _MAX_RETRIES:
            time.sleep(_RETRY_BACKOFF * attempt)

    return {"error": last_err or "Unknown error"}


def _clean_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state": rec.get("state"),
        "district": rec.get("district"),
        "market": rec.get("market"),
        "commodity": rec.get("commodity"),
        "variety": rec.get("variety"),
        "arrival": rec.get("arrival"),
        "min_price": rec.get("min_price"),
        "max_price": rec.get("max_price"),
        "modal_price": rec.get("modal_price"),
        "reported_date": rec.get("reported_date"),
    }


def get_prices(
    commodity: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
) -> Union[List[Dict[str, Any]], Dict[str, str]]:

    params = {"format": "json", "limit": limit, "offset": offset}
    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state

    result = _call_api(params)
    if isinstance(result, dict) and result.get("error"):
        return result

    return [_clean_record(r) for r in result]


def get_states(limit: int = 1000) -> Union[List[str], Dict[str, str]]:
    params = {"format": "json", "limit": limit}
    result = _call_api(params)
    if isinstance(result, dict) and result.get("error"):
        return result

    states = sorted({(rec.get("state") or "").strip() for rec in result if rec.get("state")})
    return states


def get_commodities(limit: int = 500, state: Optional[str] = None) -> Union[List[str], Dict[str, str]]:
    params = {"format": "json", "limit": limit}
    if state:
        params["filters[state]"] = state

    result = _call_api(params)
    if isinstance(result, dict) and result.get("error"):
        return result

    commodities = sorted({(rec.get("commodity") or "").strip() for rec in result if rec.get("commodity")})
    return commodities


if __name__ == "__main__":
    print("Testing get_commodities() sample...")
    out = get_commodities(limit=200)
    if isinstance(out, dict) and out.get("error"):
        print("Error:", out["error"])
    else:
        print("Sample commodities:", out[:20])
