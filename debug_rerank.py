import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from logic.engine import _normalize, _keyword_score
from logic.market_data import get_all_roles
from logic.llm import rerank_roles

user_query = "i love hacking and have a thing about ai can u suggest me some careers"
user_words = _normalize(user_query).split()

scored = []
for role in get_all_roles():
    score = _keyword_score(user_words, role)
    if score >= 0.15:
        scored.append((score, role))

scored.sort(key=lambda x: (x[0], x[1]["demand_score"]), reverse=True)
candidates = [r.copy() for _, r in scored[:8]]

print(f"Candidates before rerank: {[r['slug'] for r in candidates]}")

if len(candidates) > 2:
    final_results = rerank_roles(user_query, candidates)
    print(f"Results after rerank: {[r['slug'] for r in final_results]}")
else:
    print("Not enough candidates to rerank.")
