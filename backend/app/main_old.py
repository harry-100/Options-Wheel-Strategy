from app.strategies.put_strategy import filter_csp_candidates, covered_call_candidates
from app.data.yfinance_client import YFinanceClient
import pandas as pd
import yfinance as yf


def print_separator(title):
    print("\n" + "="*50)
    print(f" {title} ".center(50, "="))
    print("="*50)


def main():
    # Initialize client
    client = YFinanceClient()

    # Test underlying price
    ticker = "SPY"
    price = client.get_underlying_price(ticker)
    print_separator("Underlying Price")
    print(f"{ticker} Current Price: ${price:.2f}")

    # Get all available expirations
    stock = yf.Ticker(ticker)
    available_expirations = stock.options
    print_separator("Available Expirations")
    print("Available expiration dates:")
    for i, exp in enumerate(available_expirations, 1):
        print(f"{i}. {exp}")

    # You can specify your desired expiration date here
    desired_expiration = "2025-06-20"  # Change this to your desired expiration date

    # Get options for specific expiration
    print_separator(f"Options Chain for {desired_expiration}")
    options = client.get_option_chain(
        ticker, expiration_date=desired_expiration)
    calls = client.get_option_chain(
        ticker, expiration_date=desired_expiration, option_type="call")
    puts = client.get_option_chain(
        ticker, expiration_date=desired_expiration, option_type="put")

    # Clean/rename columns for compatibility
    puts_df = puts[["symbol", "strike", "expiration", "bid"]].copy()
    puts_df["type"] = "put"

    # Run CSP strategy logic
    csp_ideas = filter_csp_candidates(puts_df, price)
    print("\n=== CSP Trade Ideas ===")
    print(csp_ideas)

    # Example: Assume we already own 100 shares of SPY
    calls_df = calls[["symbol", "strike", "expiration", "bid"]].copy()
    calls_df["type"] = "call"

    assigned_position = {"current_price": price}
    covered_call_ideas = covered_call_candidates(assigned_position, calls_df)
    print("\n=== Covered Call Ideas ===")
    print(covered_call_ideas)


if __name__ == "__main__":
    main()
