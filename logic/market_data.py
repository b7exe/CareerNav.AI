import os
import json
# Triggering hot reload for dataset expansion

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'market_cache.json')

# Helper to build YouTube search links
def yt(channel, role):
    return f"https://www.youtube.com/results?search_query={channel.replace(' ', '+')}+{role.replace(' ', '+')}"

# Load roles from a separate JSON for safety and cleanliness
with open(os.path.join(os.path.dirname(__file__), 'market_data_json.json'), 'r') as f:
    DEFAULT_ROLES = json.load(f)

def _get_active_roles() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_ROLES

def get_all_roles() -> list[dict]:
    return list(_get_active_roles().values())

def get_role(slug: str) -> dict | None:
    return _get_active_roles().get(slug)
