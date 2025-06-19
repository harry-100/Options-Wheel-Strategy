import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class YFinanceClient:
    def __init__(self):
        pass

    def get_underlying_price(self, ticker):
        """
        Gets the current price of the underlying stock.
        """
        stock = yf.Ticker(ticker)
        return stock.info.get('regularMarketPrice')

    def get_option_chain(self, underlying, expiration_date=None, option_type=None):
        """
        Fetches options contracts for a ticker. Can filter by expiration and type (put/call).
        If no expiration_date is provided, uses the nearest available expiration.
        """
        stock = yf.Ticker(underlying)

        # Get all available expiration dates
        expirations = stock.options
        print(f"Available expirations: {expirations}")

        # If no expiration date provided, use the nearest one
        if not expiration_date and expirations:
            expiration_date = expirations[0]
            print(f"Using nearest expiration: {expiration_date}")

        if not expiration_date or expiration_date not in expirations:
            print(
                f"Warning: No options found for expiration {expiration_date}")
            print(f"Available expirations are: {expirations}")
            return pd.DataFrame()

        # Get options chain for the specified expiration
        opt = stock.option_chain(expiration_date)

        # Combine calls and puts
        calls = opt.calls
        puts = opt.puts

        # Add type column
        calls['type'] = 'call'
        puts['type'] = 'put'

        # Combine and filter by type if specified
        df = pd.concat([calls, puts])
        if option_type:
            df = df[df['type'].str.lower() == option_type.lower()]

        # Rename columns to match our previous format
        df = df.rename(columns={
            'contractSymbol': 'symbol',
            'strike': 'strike',
            'lastPrice': 'last_price',
            'bid': 'bid',
            'ask': 'ask',
            'volume': 'volume',
            'openInterest': 'open_interest',
            'impliedVolatility': 'implied_volatility'
        })

        # Add expiration column
        df['expiration'] = expiration_date

        # Select and reorder columns
        columns = [
            'symbol', 'strike', 'expiration', 'type', 'bid', 'ask',
            'last_price', 'volume', 'open_interest', 'implied_volatility'
        ]
        df = df[columns]

        return df

    def get_next_expiration(self, ticker):
        """
        Gets the next available expiration date for a ticker.
        """
        stock = yf.Ticker(ticker)
        expirations = stock.options
        return expirations[0] if expirations else None
