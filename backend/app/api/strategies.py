from app.strategies.wheel import filter_csp_candidates, covered_call_candidates
from fastapi import APIRouter
from app.data.polygon_client import fetch_chain, get_price, keep
import pandas as pd
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse

router = APIRouter()


def get_polygon_data(ticker, option_type="call", min_dte=7, max_dte=45):
    """
    Get options data using the standalone polygon_client functions
    """
    try:
        print(
            f"Fetching data for {ticker}, type: {option_type}, DTE: {min_dte}-{max_dte}")

        # Fetch the data with configurable parameters
        all_results = []
        contract_count = 0
        for contract in fetch_chain(ticker, contract_type=option_type, min_dte=min_dte, max_dte=max_dte):
            contract_count += 1
            # Apply the keep filter with relaxed delta constraints for wheel strategy
            if keep(contract, delta_min=0.1, delta_max=0.9, dte_min=min_dte, dte_max=max_dte):
                all_results.append(contract)

        print(
            f"Total contracts fetched: {contract_count}, filtered contracts: {len(all_results)}")

        # Convert to DataFrame format expected by the strategies
        if not all_results:
            print("No contracts passed filtering")
            return pd.DataFrame()

        df_data = []
        today_utc = datetime.now(timezone.utc).date()
        for contract in all_results:
            dte = (isoparse(contract["details"]
                   ["expiration_date"]).date() - today_utc).days

            df_data.append({
                "symbol": contract["details"]["ticker"],
                "strike": contract["details"]["strike_price"],
                "expiration": contract["details"]["expiration_date"],
                "type": contract["details"]["contract_type"],
                "bid": get_price(contract),
                "delta": contract.get("greeks", {}).get("delta"),
                "gamma": contract.get("greeks", {}).get("gamma"),
                "theta": contract.get("greeks", {}).get("theta"),
                "vega": contract.get("greeks", {}).get("vega"),
                "implied_volatility": contract.get("implied_volatility"),
                "open_interest": contract.get("open_interest", 0),
                "dte": dte
            })

        df = pd.DataFrame(df_data)
        print(f"Created DataFrame with {len(df)} rows")
        return df

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


def get_underlying_price(ticker):
    """
    Get underlying price using the polygon_client functions
    """
    try:
        # Get the first contract to estimate price
        for contract in fetch_chain(ticker, contract_type="call"):
            price = get_price(contract)
            if price is not None:
                # Estimate underlying price from option price and strike
                delta = contract.get('greeks', {}).get('delta', 0)
                strike = contract['details']['strike_price']
                if delta > 0.5:  # ITM option
                    return strike + (price / delta) if delta > 0 else strike
                return strike  # Fallback to strike price
        return None
    except Exception as e:
        print(f"Error getting underlying price for {ticker}: {e}")
        return None


@router.get("/csp/polygon")
def csp_polygon(
    ticker: str,
    min_roi: float = 1.0,
    min_dte: int = 7,
    max_dte: int = 45,
):
    print(
        f"CSP request for {ticker}, ROI: {min_roi}, DTE: {min_dte}-{max_dte}")
    df = get_polygon_data(ticker, option_type="put",
                          min_dte=min_dte, max_dte=max_dte)
    price = get_underlying_price(ticker)
    print(f"Got DataFrame with {len(df)} rows, price: {price}")
    if df.empty or price is None:
        print("Returning empty list due to empty DataFrame or no price")
        return []
    ideas = filter_csp_candidates(df, price, min_roi=min_roi, max_dte=max_dte)
    print(f"Filtered to {len(ideas)} ideas")
    return ideas.to_dict(orient="records")


@router.get("/cc/polygon")
def cc_polygon(
    ticker: str,
    min_roi: float = 1.0,
    min_dte: int = 7,
    max_dte: int = 45,
):
    print(f"CC request for {ticker}, ROI: {min_roi}, DTE: {min_dte}-{max_dte}")
    df = get_polygon_data(ticker, option_type="call",
                          min_dte=min_dte, max_dte=max_dte)
    price = get_underlying_price(ticker)
    print(f"Got DataFrame with {len(df)} rows, price: {price}")
    if df.empty or price is None:
        print("Returning empty list due to empty DataFrame or no price")
        return []
    ideas = covered_call_candidates(
        {"current_price": price}, df, min_roi=min_roi, max_dte=max_dte)
    print(f"Filtered to {len(ideas)} ideas")
    return ideas.to_dict(orient="records")

# (Optionally, comment out or remove the IB endpoints)
