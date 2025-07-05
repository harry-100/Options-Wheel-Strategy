# app/strategies/wheel.py

import datetime
import pandas as pd
import numpy as np


def calculate_dte(expiration):
    today = datetime.date.today()
    if isinstance(expiration, str):
        expiration = datetime.datetime.strptime(expiration, '%Y-%m-%d').date()
    return (expiration - today).days


def calculate_roi(premium, strike_price):
    return (premium / strike_price) * 100 if strike_price else 0


def is_otm_put(current_price, strike_price):
    return strike_price < current_price


def is_otm_call(current_price, strike_price):
    return strike_price > current_price


def filter_csp_candidates(options_df, current_price, min_roi=1.0, max_dte=15):
    """
    Filter options for ideal CSP candidates based on ROI, DTE, and OTM criteria.
    """
    results = []
    for _, row in options_df.iterrows():
        # Use DTE from the data if available, otherwise calculate it
        dte = row.get('dte', calculate_dte(row['expiration']))
        roi = calculate_roi(row['bid'], row['strike'])

        if (
            is_otm_put(current_price, row['strike']) and
            roi >= min_roi and
            dte <= max_dte and
            row['bid'] is not None  # Ensure we have a valid price
        ):
            results.append({
                "symbol": row['symbol'],
                "strike": row['strike'],
                "expiration": row['expiration'],
                "bid": row['bid'],
                "roi_%": round(roi, 2),
                "dte": dte,
                "delta": row.get('delta'),
                "gamma": row.get('gamma'),
                "theta": row.get('theta'),
                "vega": row.get('vega'),
                "implied_volatility": row.get('implied_volatility'),
                "open_interest": row.get('open_interest', 0)
            })

    return pd.DataFrame(results)


def should_roll_or_close(position, current_price):
    """
    Simple rules:
    - Close if 90% profit
    - Roll if option is ITM and expiration <= 3 days
    """
    dte = calculate_dte(position['expiration'])
    is_itm = current_price < position['strike'] if position['type'] == "put" else current_price > position['strike']
    profit_pct = position.get("profit_pct", 0)

    if profit_pct >= 90:
        return "Close"
    elif is_itm and dte <= 3:
        return "Roll"
    else:
        return "Hold"


def covered_call_candidates(assigned_stock_df, call_options_df, min_roi=1.0, max_dte=15):
    """
    Suggest covered calls for assigned shares.
    """
    current_price = assigned_stock_df['current_price']
    results = []
    for _, row in call_options_df.iterrows():
        # Use DTE from the data if available, otherwise calculate it
        dte = row.get('dte', calculate_dte(row['expiration']))
        roi = calculate_roi(row['bid'], current_price)

        if (
            is_otm_call(current_price, row['strike']) and
            roi >= min_roi and
            dte <= max_dte and
            row['bid'] is not None  # Ensure we have a valid price
        ):
            results.append({
                "symbol": row['symbol'],
                "strike": row['strike'],
                "expiration": row['expiration'],
                "bid": row['bid'],
                "roi_%": round(roi, 2),
                "dte": dte,
                "delta": row.get('delta'),
                "gamma": row.get('gamma'),
                "theta": row.get('theta'),
                "vega": row.get('vega'),
                "implied_volatility": row.get('implied_volatility'),
                "open_interest": row.get('open_interest', 0)
            })

    return pd.DataFrame(results)
