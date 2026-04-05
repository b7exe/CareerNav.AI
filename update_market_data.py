import json
import os

d = json.load(open('market_data_updated.json'))
content = f"""import os
import json

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'market_cache.json')

# Helper to build YouTube search links
def yt(channel, role):
    return f"https://www.youtube.com/results?search_query={{channel.replace(' ', '+')}}+{{role.replace(' ', '+')}}"

DEFAULT_ROLES = {json.dumps(d, indent=4)}

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
"""

with open('logic/market_data.py', 'w') as f:
    f.write(content)
