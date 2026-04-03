import sys
import os

# Add the current directory to sys.path so we can import logic
sys.path.append(os.getcwd())

from logic.engine import _normalize, _keyword_score
from logic.market_data import get_all_roles

user_query = "i love hacking and have a thing about ai can u suggest me some careers"
user_words = _normalize(user_query).split()

print(f"User words: {user_words}")

scored = []
for role in get_all_roles():
    score = _keyword_score(user_words, role)
    if score > 0:
        scored.append((score, role['title'], role['match_keywords']))

scored.sort(key=lambda x: x[0], reverse=True)

for score, title, kws in scored:
    print(f"Score: {score:.4f} | Role: {title} | KWs: {kws}")
