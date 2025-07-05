"""
polygon_client.py
────────────────────────────────────────────────────────
Fetch call-option contracts for a given underlying that meet
  • delta  between 0.15 and 0.25
  • DTE    between 10   and 45 calendar days

Displays a single Price column:
  • last trade price if available
  • otherwise mid-quote ( (bid + ask) / 2 )
  • None if neither is present

Prereqs:  pip install requests python-dateutil
"""

from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import requests
import sys
import textwrap

# ── CONFIG ──────────────────────────────────────────────────────────────────
# ← paste your Options Starter key here
API_KEY = "hOv5_WV8jKS0In3j1BW6Nmom1Z3W3mrN"
TICKER = "AAPL"  # ← underlying symbol to screen

DELTA_MIN, DELTA_MAX = 0.15, 0.50     # delta window
DTE_MIN,   DTE_MAX = 10,   45       # days-to-expiration window
# ────────────────────────────────────────────────────────────────────────────

# ── helper: ensure every URL carries apiKey=… ───────────────────────────────


def add_key(url: str) -> str:
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query))
    q["apiKey"] = API_KEY
    return urlunparse(parsed._replace(query=urlencode(q)))


HEADERS = {"Authorization": f"Bearer {API_KEY}"}  # redundant but robust

# ── date boundaries for server-side filtering ───────────────────────────────
today_utc = datetime.now(timezone.utc).date()
min_expdate = (today_utc + timedelta(days=DTE_MIN)).isoformat()
max_expdate = (today_utc + timedelta(days=DTE_MAX)).isoformat()

# ── fetch the chain, paging via cursor links ────────────────────────────────


def fetch_chain(ticker: str, contract_type="call", min_dte=None, max_dte=None):
    """
    Fetch options chain with configurable parameters
    """
    # Use provided parameters or defaults
    if min_dte is None:
        min_dte = DTE_MIN
    if max_dte is None:
        max_dte = DTE_MAX

    # Update date boundaries
    today_utc = datetime.now(timezone.utc).date()
    min_expdate = (today_utc + timedelta(days=min_dte)).isoformat()
    max_expdate = (today_utc + timedelta(days=max_dte)).isoformat()

    base = f"https://api.polygon.io/v3/snapshot/options/{ticker}"
    params = {
        "contract_type": contract_type,
        "expiration_date.gte": min_expdate,
        "expiration_date.lte": max_expdate,
        "limit": 250,
        "apiKey": API_KEY,
    }

    url = base
    while url:
        resp = requests.get(
            url,
            params=params if url == base else None,
            headers=HEADERS,
            timeout=15,
        )

        # Early exit on bad key or plan mismatch
        if resp.status_code == 401:
            sys.exit(
                textwrap.dedent(
                    f"""
                    ❌ 401 Unauthorized
                    → Check your API key and that your plan includes
                      /v3/snapshot/options with Greeks.
                    → Response: {resp.text[:200]}
                    """
                )
            )

        resp.raise_for_status()
        body = resp.json()
        yield from body.get("results", [])

        url = body.get("next_url")
        if url:
            url = add_key(url)    # re-attach the key for every cursor page
        params = None             # only first request uses params

# ── delta & DTE filter ──────────────────────────────────────────────────────


def keep(contract: dict, delta_min=None, delta_max=None, dte_min=None, dte_max=None):
    """
    Filter contract with configurable parameters
    """
    # Use provided parameters or defaults
    if delta_min is None:
        delta_min = DELTA_MIN
    if delta_max is None:
        delta_max = DELTA_MAX
    if dte_min is None:
        dte_min = DTE_MIN
    if dte_max is None:
        dte_max = DTE_MAX

    delta = (contract.get("greeks") or {}).get("delta")
    if delta is None or not (delta_min <= delta <= delta_max):
        return False

    today_utc = datetime.now(timezone.utc).date()
    dte = (
        isoparse(contract["details"]["expiration_date"]).date() - today_utc
    ).days
    if not (dte_min <= dte <= dte_max):
        return False

    contract["_delta"] = delta
    contract["_dte"] = dte
    return True

# ── price helper (trade price ▸ mid-quote ▸ None) ───────────────────────────


def get_price(c: dict):
    trade_px = (c.get("last_trade") or {}).get("price")
    if trade_px is not None:
        return trade_px
    q = c.get("last_quote") or {}
    bid, ask = q.get("bid_price"), q.get("ask_price")
    if bid is not None and ask is not None:
        return round((bid + ask) / 2, 4)
    return None

# ── pretty-printer ──────────────────────────────────────────────────────────


def fmt(c: dict) -> str:
    d = c["details"]
    return (
        f"{d['ticker']:>20}  Δ={c['_delta']:+.3f}  "
        f"DTE={c['_dte']:>2}  Strike={d['strike_price']:<8}  "
        f"Price={get_price(c)}"
    )


# ── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(
        f"Fetching {TICKER} calls "
        f"(Δ {DELTA_MIN}-{DELTA_MAX}, DTE {DTE_MIN}-{DTE_MAX}) …"
    )

    matches = [c for c in fetch_chain(TICKER) if keep(c)]

    print(f"Found {len(matches)} matching contracts:\n")
    for c in sorted(
        matches, key=lambda x: (x["_dte"], x["details"]["strike_price"])
    ):
        print(fmt(c))
