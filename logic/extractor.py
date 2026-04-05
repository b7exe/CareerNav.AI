import time
import json
import threading
import random
import os
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'market_cache.json')

def simulate_realtime_extraction():
    """
    Executes real-time data fetching in the background.
    """
    from logic.realtime_fetcher import fetch_live_market_data
    
    print("[Extractor] Starting live API fetch sequence...")
    current_data = fetch_live_market_data()
        
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(current_data, f, indent=4)
        print(f"[Extractor] Live data refreshed and written to {CACHE_FILE}")
    except Exception as e:
        print(f"[Extractor Error] Failed to write cache: {e}")


def _extraction_loop():
    print("[Extractor Daemon] Booting up 10-hour asynchronous pipeline.")
    while True:
        simulate_realtime_extraction()
        # Sleep for exactly 10 hours (10 * 60 * 60 = 36000 seconds)
        time.sleep(36000)


def init_background_job():
    """
    Spins up the extraction engine in a Daemon thread.
    This guarantees the loop runs continuously without blocking Flask processes.
    """
    thread = threading.Thread(target=_extraction_loop, daemon=True)
    thread.start()
