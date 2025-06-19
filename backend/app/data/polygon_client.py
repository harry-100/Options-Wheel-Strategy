# app/data/polygon_client.py

import os
import requests
from dotenv import load_dotenv
import pandas as pd

# Get the project root directory (2 levels up from this file)
ROOT_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"


class PolygonClient:
    def __init__(self, api_key=POLYGON_API_KEY):
        self.api_key = api_key

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        params["apiKey"] = self.api_key
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_underlying_price(self, ticker):
        """
        Gets the current price of the underlying using the v3 snapshot endpoint.
        This endpoint is available in the Options Starter plan.
        """
        endpoint = f"/v3/snapshot/options/{ticker}"
        data = self._get(endpoint)
        # Get the first option contract to extract the underlying price
        if data.get('results') and len(data['results']) > 0:
            # The underlying price can be derived from the option's delta and strike price
            # For deep ITM calls (delta > 0.99), the underlying price is approximately the strike price
            for option in data['results']:
                if option.get('greeks', {}).get('delta', 0) > 0.99:
                    return option['details']['strike_price']
        return None

    def get_option_chain(self, underlying, expiration_date=None, option_type=None):
        """
        Fetches options contracts for a ticker. Can filter by expiration and type (put/call).
        If no expiration_date is provided, uses the nearest available expiration.
        """
        endpoint = f"/v3/snapshot/options/{underlying}"
        data = self._get(endpoint)
        results = data.get("results", [])
        print(f"Total options found: {len(results)}")

        # Get available expiration dates
        available_expirations = sorted(
            set(opt["details"]["expiration_date"] for opt in results))
        print(f"Available expirations: {available_expirations}")

        # If no expiration date provided, use the nearest one
        if not expiration_date and available_expirations:
            expiration_date = available_expirations[0]
            print(f"Using nearest expiration: {expiration_date}")

        # Optional filtering
        if expiration_date:
            print(f"Filtering for expiration: {expiration_date}")
            results = [opt for opt in results if opt["details"]
                       ["expiration_date"] == expiration_date]
            print(f"Options after expiration filter: {len(results)}")

            if len(results) == 0:
                print(
                    f"Warning: No options found for expiration {expiration_date}")
                print(f"Available expirations are: {available_expirations}")
                return pd.DataFrame()

        if option_type:
            print(f"Filtering for option type: {option_type}")
            results = [opt for opt in results if opt["details"]
                       ["contract_type"].lower() == option_type.lower()]
            print(f"Options after type filter: {len(results)}")

        # Convert to DataFrame
        df = pd.DataFrame([{
            "symbol": opt["details"]["ticker"],
            "strike": opt["details"]["strike_price"],
            "expiration": opt["details"]["expiration_date"],
            "type": opt["details"]["contract_type"],
            "delta": opt.get("greeks", {}).get("delta"),
            "gamma": opt.get("greeks", {}).get("gamma"),
            "theta": opt.get("greeks", {}).get("theta"),
            "vega": opt.get("greeks", {}).get("vega"),
            "implied_volatility": opt.get("implied_volatility"),
            "open_interest": opt.get("open_interest", 0)
        } for opt in results])

        return df
