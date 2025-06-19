from app.data.options_scanner import scan_options
from fastapi import APIRouter, Query
from app.strategies.wheel import filter_csp_candidates, covered_call_candidates
import yfinance as yf
import pandas as pd
import datetime

router = APIRouter()


@router.get("/csp")
def get_cash_secured_puts(
    ticker: str,
    min_roi: float = Query(1.0, ge=0.1),
    min_dte: int = Query(7, ge=1),
    max_dte: int = Query(45, ge=1)
):
    yf_ticker = yf.Ticker(ticker.upper())
    price = yf_ticker.history(period="1d")["Close"].iloc[-1]

    csp_df = scan_options(
        yf_ticker=yf_ticker,
        option_type="put",
        current_price=price,
        strategy_func=filter_csp_candidates,
        min_roi=min_roi,
        min_dte=min_dte,
        max_dte=max_dte
    )

    return csp_df.to_dict(orient="records")


# @router.get("/csp")
# def get_cash_secured_puts(
#     ticker: str,
#     min_roi: float = Query(1.0, ge=0.1),
#     min_dte: int = Query(7, ge=1),
#     max_dte: int = Query(45, ge=1)
# ):
#     yf_ticker = yf.Ticker(ticker.upper())
#     price = yf_ticker.history(period="1d")["Close"].iloc[-1]
#     expiration_dates = yf_ticker.options

#     if not expiration_dates:
#         return {"error": "No options available for this ticker"}

#     all_puts = []

#     for exp_str in expiration_dates:
#         try:
#             exp_date = pd.to_datetime(exp_str).date()
#             dte = (exp_date - datetime.date.today()).days
#             if not (min_dte <= dte <= max_dte):
#                 continue

#             chain = yf_ticker.option_chain(exp_str)
#             puts = chain.puts[["contractSymbol", "strike", "bid"]].copy()
#             puts.columns = ["symbol", "strike", "bid"]
#             puts["expiration"] = exp_date
#             puts["type"] = "put"

#             filtered = filter_csp_candidates(
#                 puts, price, min_roi=min_roi, max_dte=max_dte)
#             all_puts.append(filtered)

#         except Exception as e:
#             print(f"Failed to load options for {exp_str}: {e}")

#     combined_df = pd.concat(
#         all_puts, ignore_index=True) if all_puts else pd.DataFrame()
#     return combined_df.to_dict(orient="records")


@router.get("/cc")
def get_covered_calls(
    ticker: str,
    min_roi: float = Query(1.0, ge=0.1),
    min_dte: int = Query(7, ge=1),
    max_dte: int = Query(45, ge=1)
):
    yf_ticker = yf.Ticker(ticker.upper())
    price = yf_ticker.history(period="1d")["Close"].iloc[-1]

    cc_df = scan_options(
        yf_ticker=yf_ticker,
        option_type="call",
        current_price=price,
        strategy_func=lambda df, price, **kwargs: covered_call_candidates(
            {"current_price": price}, df, **kwargs),
        min_roi=min_roi,
        min_dte=min_dte,
        max_dte=max_dte
    )

    return cc_df.to_dict(orient="records")
