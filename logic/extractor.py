import time
import json
import threading
import random
import os
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'market_cache.json')

def simulate_realtime_extraction():
    """
    Simulates fetching job volume from LinkedIn/Glassdoor
    and social sentiment from Reddit/X.
    We apply a volatility modifier to simulate live dynamic updates.
    """
    # Import locally to avoid circular dependencies
    from logic.market_data import DEFAULT_ROLES
    import copy
    
    current_data = copy.deepcopy(DEFAULT_ROLES)
    
    for slug, role in current_data.items():
        # Inject randomized volatility simulating live API updates
        volatility_demand = random.randint(-2, 2)
        volatility_social = random.randint(-3, 3)
        
        role['demand_score'] = max(0, min(100, role['demand_score'] + volatility_demand))
        role['social_signal'] = max(0, min(100, role['social_signal'] + volatility_social))
        role['last_updated'] = datetime.utcnow().isoformat()
        
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
