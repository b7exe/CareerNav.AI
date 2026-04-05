import os
import json
import requests
import concurrent.futures
from flask import Flask
from dotenv import load_dotenv

# Load ENV
load_dotenv()

def check_section_1():
    print("=== SECTION 1: CORE APP HEALTH ===")
    # 1. Startup check (mock)
    try:
        from app import app
        print("[PASS] app.py imported without errors")
    except Exception as e:
        print(f"[FAIL] app.py import failed: {e}")

    # 2. Env vars
    keys = ["NVIDIA_API_KEY", "GEMINI_API_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY", "NEWS_API_KEY"]
    for k in keys:
        if os.getenv(k):
            print(f"[PASS] {k} is set")
        else:
            print(f"[WARN] {k} is MISSING")

    # 3. .env and .gitignore
    if os.path.exists(".env"): print("[PASS] .env exists")
    else: print("[FAIL] .env missing")
    
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            if ".env" in f.read(): print("[PASS] .gitignore includes .env")
            else: print("[FAIL] .gitignore missing .env")
    
    # 4. Requirements
    try:
        with open("requirements.txt", "r") as f:
            reqs = f.read()
            deps = ["Flask", "gunicorn", "openai", "python-dotenv", "requests"]
            for d in deps:
                if d.lower() in reqs.lower(): print(f"[PASS] requirements.txt includes {d}")
                else: print(f"[FAIL] requirements.txt missing {d}")
    except: print("[FAIL] Could not read requirements.txt")

def check_section_3():
    print("\n=== SECTION 3: MARKET DATA VERIFICATION ===")
    from logic.market_data import get_all_roles
    roles = get_all_roles()
    print(f"Total roles: {len(roles)}")
    
    fields = ["title", "category", "description", "why_now", "core_skills", "emerging_skills", 
              "avg_salary_india", "global_demand", "ai_disruption_risk", "situation", "scope", 
              "lifetime", "match_keywords", "youtube_resources"]
    
    fail_roles = []
    for r in roles:
        missing = [f for f in fields if f not in r or not r[f]]
        if missing:
            fail_roles.append((r.get('slug', 'unknown'), missing))
            
    if not fail_roles: print("[PASS] All roles have all 14 required fields")
    else:
        for slug, m in fail_roles:
            print(f"[FAIL] Role '{slug}' missing: {m}")

def check_section_4():
    print("\n=== SECTION 4: MATCHING ENGINE VERIFICATION ===")
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
        ("", "software-architect"),
        ("I want to earn the most money possible in IT", "software-architect")
    ]
    
    for query, expected in tests:
        res = analyze_interests(query, top_n=3)
        slugs = [r['slug'] for r in res]
        match = any(expected in s for s in slugs)
        status = "PASS" if match else "FAIL"
        print(f"Query: '{query}' -> Found: {slugs[:3]} -> {status}")

def check_section_6():
    print("\n=== SECTION 6: DATA SOURCES VERIFICATION ===")
    from logic.data_sources import fetch_adzuna, fetch_github_trending, fetch_newsapi, fetch_remoteok, fetch_hackernews
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        f_adz = executor.submit(fetch_adzuna, ["python"], "hyderabad")
        f_git = executor.submit(fetch_github_trending)
        f_news = executor.submit(fetch_newsapi)
        f_rok = executor.submit(fetch_remoteok)
        f_hn = executor.submit(fetch_hackernews)
        
        try:
            print(f"Adzuna: {len(f_adz.result(timeout=5))} jobs")
            print("[PASS] Adzuna OK")
        except: print("[FAIL] Adzuna")
        
        try:
            print(f"GitHub: {len(f_git.result(timeout=5))} repos")
            print("[PASS] GitHub OK")
        except: print("[FAIL] GitHub")
        
        try:
            print(f"News: {len(f_news.result(timeout=5))} articles")
            print("[PASS] NewsAPI OK")
        except: print("[FAIL] NewsAPI")
        
        try:
            print(f"RemoteOK: {len(f_rok.result(timeout=5))} jobs")
            print("[PASS] RemoteOK OK")
        except: print("[FAIL] RemoteOK")
        
        try:
            print(f"HN: {len(f_hn.result(timeout=5))} signals")
            print("[PASS] HN OK")
        except: print("[FAIL] HN")

if __name__ == "__main__":
    check_section_1()
    check_section_3()
    check_section_4()
    check_section_6()
