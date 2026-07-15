import json
import os

MARKET_HOURS_PATH = "/home/kidpixel/trading_automation-main/configs/market_hours.json"

# New assets to add and their details
# Since all these are European assets listed on Xetra, Euronext, Milan, or Madrid,
# they all have standard European trading hours: 09:00 to 17:30 CET, offset +01:00.
NEW_ASSETS_HOURS = {
    "dpwdeeur": {
        "exchange": "XETRA",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "teniteur": {
        "exchange": "ITALIAN_STOCK_EXCHANGE",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "akzanleur": {
        "exchange": "EURONEXT_AMSTERDAM",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "daideeur": {
        "exchange": "XETRA",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "mrkdeeur": {
        "exchange": "XETRA",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "vnadeeur": {
        "exchange": "XETRA",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "acfreur": {
        "exchange": "EURONEXT_PARIS",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "lxsdeeur": {
        "exchange": "XETRA",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "randnleur": {
        "exchange": "EURONEXT_AMSTERDAM",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "rifreur": {
        "exchange": "EURONEXT_PARIS",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "abibeeur": {
        "exchange": "EURONEXT_BRUSSELS",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "belgbeeur": {
        "exchange": "EURONEXT_BRUSSELS",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    },
    "cafreur": {
        "exchange": "EURONEXT_PARIS",
        "open": "09:00",
        "close": "17:30",
        "tz_offset": "+01:00"
    }
}

def main():
    if not os.path.exists(MARKET_HOURS_PATH):
        print(f"Error: {MARKET_HOURS_PATH} not found.")
        return

    with open(MARKET_HOURS_PATH, "r") as f:
        market_hours = json.load(f)

    updated = False
    for asset, details in NEW_ASSETS_HOURS.items():
        if asset not in market_hours:
            market_hours[asset] = details
            print(f"Adding {asset} with exchange {details['exchange']}...")
            updated = True
        else:
            print(f"{asset} already present in market hours.")

    if updated:
        with open(MARKET_HOURS_PATH, "w") as f:
            json.dump(market_hours, f, indent=2)
        print("Updated market_hours.json successfully.")
    else:
        print("No updates needed.")

if __name__ == "__main__":
    main()
