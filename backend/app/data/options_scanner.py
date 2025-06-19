# app/data/options_scanner.py

import datetime
import pandas as pd


def scan_options(
    yf_ticker,
    option_type: str,
    current_price: float,
    strategy_func,
    min_roi: float,
    min_dte: int,
    max_dte: int
):
    """
    Generic scanner for CSP or CC using yfinance ticker and strategy logic.
    """
    results = []
    expiration_dates = yf_ticker.options

    for exp_str in expiration_dates:
        try:
            exp_date = pd.to_datetime(exp_str).date()
            dte = (exp_date - datetime.date.today()).days
            if not (min_dte <= dte <= max_dte):
                continue

            chain = yf_ticker.option_chain(exp_str)
            if option_type == "put":
                options_df = chain.puts[[
                    "contractSymbol", "strike", "bid"]].copy()
            else:
                options_df = chain.calls[[
                    "contractSymbol", "strike", "bid"]].copy()

            options_df.columns = ["symbol", "strike", "bid"]
            options_df["expiration"] = exp_date
            options_df["type"] = option_type

            filtered_df = strategy_func(
                options_df,
                current_price,
                min_roi=min_roi,
                max_dte=max_dte
            )
            results.append(filtered_df)

        except Exception as e:
            print(f"Failed to load {option_type} options for {exp_str}: {e}")

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
