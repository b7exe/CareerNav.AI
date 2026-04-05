import os
import requests
import json
import concurrent.futures
from dotenv import load_dotenv

# Load ENV
load_dotenv()

def check_env():
    print("=== SECTION 1: ENV CHECK ===")
    keys = ["NVIDIA_API_KEY", "GEMINI_API_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY", "NEWS_API_KEY"]
    for k in keys:
        val = os.getenv(k)
        if val:
            print(f"[PASS] {k} is set (starts with {val[:4]}...)")
        else:
            print(f"[WARN] {k} is MISSING")

def check_market_data():
    print("\n=== SECTION 3: MARKET DATA CHECK ===")
    from logic.market_data import get_all_roles
    roles = get_all_roles()
    print(f"Total roles found: {len(roles)}")
    
    required_fields = [
        "title", "category", "description", "why_now", "core_skills",
        "emerging_skills", "avg_salary_india", "global_demand",
        "ai_disruption_risk", "situation", "scope", "lifetime",
        "match_keywords", "youtube_resources"
    ]
    
    missing_data = []
    empty_keywords = []
    
    for r in roles:
        missing = [f for f in required_fields if not r.get(f)]
        if missing:
            missing_data.append(f"{r.get('slug')} missing: {missing}")
        
        kws = r.get("match_keywords", [])
        if not kws:
            empty_keywords.append(r.get("slug"))
            
    if not missing_data: print("[PASS] All roles have all required fields")
    else: 
        for m in missing_data: print(f"[FAIL] {m}")
        
    if not empty_keywords: print("[PASS] All roles have match_keywords")
    else: print(f"[FAIL] Roles with empty keywords: {empty_keywords}")

def check_engine():
    print("\n=== SECTION 4: ENGINE CHECK ===")
    from logic.engine import analyze_interests
    
    tests = [
        ("I want to manage engineers", "engineering-manager"),
        ("I want to build games", "game-developer"),
        ("How do I get into prompt engineering", "prompt-engineering"),
        ("I like automation and CI/CD pipelines", "devops"),
        ("I want to learn Rust", "rust"),
        ("I want to work in cybersecurity", "cyber-security-analyst"),
        ("I like building mobile apps", "mobile-developer"),
        ("I want to work with AI and machine learning", "ai-engineer"),
        ("", "software-architect") # Testing default/no-idea
    ]
    
    for query, expected_slug in tests:
        results = analyze_interests(query, top_n=3)
        slugs = [r.get('slug') for r in results]
        pass_fail = "PASS" if expected_slug in slugs or any(expected_slug in s for s in slugs) else "FAIL"
        # Special check for empty query which returns hot roles
        if not query and results: pass_fail = "PASS"
        
        print(f"Query: '{query}'")
        print(f"Results: {[(r.get('slug'), r.get('match_reason')) for r in results]}")
        print(f"Expected: {expected_slug} | Result: {pass_fail}")
        print("-" * 20)

def check_data_sources():
    print("\n=== SECTION 6: DATA SOURCES CHECK ===")
    from logic.data_sources import fetch_adzuna, fetch_github_trending, fetch_newsapi, fetch_remoteok, fetch_hackernews
    
    print("Testing Adzuna...")
    try:
        adz = fetch_adzuna(["python"], "hyderabad")
        print(f"[DATA] Adzuna returned {len(adz)} jobs")
    except Exception as e: print(f"[FAIL] Adzuna error: {e}")

    print("Testing GitHub...")
    try:
        git = fetch_github_trending()
        print(f"[DATA] GitHub returned {len(git)} repos")
    except Exception as e: print(f"[FAIL] GitHub error: {e}")

    print("Testing NewsAPI...")
    try:
        news = fetch_newsapi()
        print(f"[DATA] NewsAPI returned {len(news)} articles")
    except Exception as e: print(f"[FAIL] NewsAPI error: {e}")

    print("Testing RemoteOK...")
    try:
        rok = fetch_remoteok()
        print(f"[DATA] RemoteOK returned {len(rok)} jobs")
    except Exception as e: print(f"[FAIL] RemoteOK error: {e}")

    print("Testing Algolia HN...")
    try:
        hn = fetch_hackernews()
        print(f"[DATA] HN Algolia returned {len(hn)} comments")
    except Exception as e: print(f"[FAIL] HN error: {e}")

if __name__ == "__main__":
    check_env()
    check_market_data()
    check_engine()
    check_data_sources()
