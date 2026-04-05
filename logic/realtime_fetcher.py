import requests
from datetime import datetime
from logic.market_data import DEFAULT_ROLES

def fetch_live_market_data():
    """
    Fetches real-world data from the HackerNews Algolia API
    to determine live demand and social signal trends.
    """
    data = {}

    with requests.Session() as session:
        for slug, role in DEFAULT_ROLES.items():
            role_copy = role.copy()

            keyword = role.get("match_keywords", [slug])[0]

            try:
                # Query HN Algolia API for mentions of the keyword
                url = f"https://hn.algolia.com/api/v1/search?query={keyword}&tags=story&hitsPerPage=1"
                resp = session.get(url, timeout=5)
                
                if resp.status_code == 200:
                    hits = resp.json().get("nbHits", 0)
                    
                    # Normalize hits to a shift score (-5 to +15)
                    # Ex: 15,000 hits -> +10 shift
                    demand_shift = int(min(15, hits / 1000) - 5)
                    social_shift = int(min(15, hits / 800) - 5)
                else:
                    demand_shift = 0
                    social_shift = 0
            except Exception as e:
                print(f"[Realtime Fetcher Error] Failed for {slug}: {e}")
                demand_shift = 0
                social_shift = 0

            role_copy["demand_score"] = max(0, min(100, role.get("demand_score", 85) + demand_shift))
            role_copy["social_signal"] = max(0, min(100, role.get("social_signal", 85) + social_shift))
            role_copy["last_updated"] = datetime.utcnow().isoformat()

            data[slug] = role_copy

    return data