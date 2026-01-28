from core.mt5_downloader import run_download_from_config
import sys
import os

days_to_download = 1000 # attempting 3 years
symbols = ['TM_VOLATILITY_100', 'TM_VOLATILITY_75', 'TM_VOLATILITY_50']
timeframe = '15m'

print(f"Downloading {days_to_download} days of data for {symbols}...")

for symbol in symbols:
    print(f"Processing {symbol}...")
    try:
        path = run_download_from_config(
            symbol=symbol,
            timeframe=timeframe,
            days=days_to_download
        )
        if path:
            print(f"[SUCCESS] Downloaded {symbol} to {path}")
        else:
            print(f"[ERROR] Failed to download {symbol}")
    except Exception as e:
        print(f"[EXCEPTION] Error downloading {symbol}: {e}")

print("Download sequence completed.")
