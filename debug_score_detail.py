import sys
import os
from difflib import SequenceMatcher

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from logic.engine import _normalize
from logic.market_data import get_all_roles

user_query = "i love hacking and have a thing about ai can u suggest me some careers"
user_words = _normalize(user_query).split()

for role in get_all_roles():
    keywords = role["match_keywords"]
    user_text = " ".join(user_words)
    
    exact_hits = sum(1 for kw in keywords if kw in user_text)
    
    fuzzy_hits = 0
    fuzzy_details = []
    for word in user_words:
        if len(word) < 3:
            continue
        for kw in keywords:
            if word in kw or kw in word:
                fuzzy_hits += 1
                fuzzy_details.append(f"Sub: {word} <-> {kw}")
                break
            ratio = SequenceMatcher(None, word, kw).ratio()
            if ratio > 0.8:
                fuzzy_hits += ratio
                fuzzy_details.append(f"Ratio {ratio:.2f}: {word} <-> {kw}")
                break

    if exact_hits > 0 or fuzzy_hits > 0:
        print(f"Role: {role['title']}")
        print(f"  Exact: {exact_hits}")
        print(f"  Fuzzy: {fuzzy_hits} ({fuzzy_details})")
        
