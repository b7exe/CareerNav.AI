import os
import time
import requests
import re
from datetime import datetime, timedelta
import concurrent.futures

def extract_skills_from_text(text: str) -> list[str]:
    if not text:
        return []
    keywords = ["Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS", "Azure", 
                "GCP", "Docker", "Kubernetes", "SQL", "MongoDB", "PostgreSQL", "Java", 
                "Spring Boot", "Go", "Rust", "AI", "ML", "LLM", "FastAPI", "GraphQL", 
                "Redis", "Kafka", "Terraform", "CI/CD", "Git", "Linux", "Cybersecurity",
                "DevOps", "Data Science", "Deep Learning", "NLP", "Computer Vision",
                "Flutter", "React Native", "Next.js", "Django", "Ruby on Rails", "PHP"]
    
    text_lower = text.lower()
    found = []
    # For some keywords like "C" or exact casing, lower might be tricky, but this list is mostly robust.
    # To be safer:
    for kw in keywords:
        # Regex word boundary for alphanumeric keywords
        if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower):
            found.append(kw)
        elif kw.lower() == "ci/cd" and "ci/cd" in text_lower:
            found.append(kw)
    return list(set(found))

def fetch_adzuna(skills: list[str], location: str) -> list[dict]:
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []
        
    query = "+".join(skills) if skills else "developer"
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={app_id}&app_key={app_key}&what={query}&where={location}&results_per_page=10&content-type=application/json"
    
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        
        jobs = []
        for r in results:
            min_sal = r.get("salary_min")
            max_sal = r.get("salary_max")
            salary_str = f"₹{min_sal/100000:.1f}L - ₹{max_sal/100000:.1f}L" if min_sal and max_sal else "Not specified"
            
            jobs.append({
                "title": r.get("title", ""),
                "company": r.get("company", {}).get("display_name", ""),
                "salary": salary_str,
                "skills_required": extract_skills_from_text(r.get("description", "")),
                "source": "adzuna",
                "url": r.get("redirect_url", "")
            })
        return jobs
    except Exception:
        return []

def fetch_github_trending() -> list[dict]:
    date_30_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    url = f"https://api.github.com/search/repositories?q=created:>{date_30_days_ago}&sort=stars&order=desc&per_page=10"
    
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        
        trending = []
        for i in items:
            trending.append({
                "name": i.get("name", ""),
                "stars": i.get("stargazers_count", 0),
                "language": i.get("language", ""),
                "why_relevant": i.get("description", "")[:100] if i.get("description") else ""
            })
        return trending
    except Exception:
        return []

def fetch_newsapi(query: str = "IT hiring India software engineer demand 2026") -> list[dict]:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []
    
    # Safe URL encode the query
    from urllib.parse import quote_plus
    safe_query = quote_plus(query)
    
    url = f"https://newsapi.org/v2/everything?q={safe_query}&sortBy=publishedAt&pageSize=5&language=en&apiKey={api_key}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        
        news = []
        for a in articles:
            news.append({
                "headline": a.get("title", ""),
                "summary": a.get("description", "")[:150] if a.get("description") else "",
                "source": a.get("source", {}).get("name", ""),
                "date": a.get("publishedAt", "")
            })
        return news
    except Exception:
        return []

def fetch_remoteok() -> list[dict]:
    url = "https://remoteok.com/api?tags=dev"
    headers = {"User-Agent": "CareerNavigatorApp/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        
        # First item is standard legal / attribution, jobs start at index 1
        data = resp.json()
        if isinstance(data, list) and len(data) > 0 and 'legal' in data[0]:
            data = data[1:]
            
        jobs = []
        for item in data[:8]:
            jobs.append({
                "title": item.get("position", ""),
                "company": item.get("company", ""),
                "salary": item.get("salary", "Not specified").replace("Â", ""), # Fix common remoteok encoding
                "skills_required": item.get("tags", []),
                "source": "remoteok",
                "url": item.get("url", "")
            })
        return jobs
    except Exception:
        return []

def fetch_hackernews() -> list[str]:
    """
    Search HN for 'Who is hiring' thread using Algolia, then get top comments.
    Single-call search is 100x faster than the old Firebase ID iteration.
    """
    try:
        # Step 1: Find the latest 'Who is hiring' story
        search_url = "https://hn.algolia.com/api/v1/search?query=Ask+HN+Who+is+hiring&tags=story&hitsPerPage=1"
        search_resp = requests.get(search_url, timeout=3)
        search_resp.raise_for_status()
        hits = search_resp.json().get("hits", [])
        
        if not hits:
            return []
            
        object_id = hits[0].get("objectID")
        if not object_id:
            return []
            
        # Step 2: Fetch top 5 comments as 'hiring signals'
        comment_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{object_id}&hitsPerPage=5"
        comment_resp = requests.get(comment_url, timeout=3)
        comment_resp.raise_for_status()
        comment_hits = comment_resp.json().get("hits", [])
        
        signals = []
        for hit in comment_hits:
            text = hit.get("comment_text", "")
            if text:
                # Basic strip HTML and truncate
                clean_text = re.sub('<[^<]+>', '', text)
                signals.append(clean_text[:300] + "...")
        return signals
    except Exception:
        return []

def get_market_context(user_skills: list[str], location: str) -> dict:
    context = {
        "timestamp": datetime.now().isoformat(),
        "location": location,
        "liveJobs": [],
        "trendingTechnologies": [],
        "marketArticles": [],
        "hiringSignals": [],
        "dataFreshness": {
            "jobs_fetched_at": "",
            "articles_fetched_at": "",
            "trending_fetched_at": ""
        }
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        f_adzuna = executor.submit(fetch_adzuna, user_skills, location)
        f_github = executor.submit(fetch_github_trending)
        f_news = executor.submit(fetch_newsapi)
        f_remoteok = executor.submit(fetch_remoteok)
        f_hn = executor.submit(fetch_hackernews)
        
        try:
            adzuna_jobs = f_adzuna.result(timeout=6)
        except Exception:
            adzuna_jobs = []
            
        try:
            remote_jobs = f_remoteok.result(timeout=6)
        except Exception:
            remote_jobs = []
            
        try:
            trending = f_github.result(timeout=6)
        except Exception:
            trending = []
            
        try:
            news = f_news.result(timeout=6)
        except Exception:
            news = []
            
        try:
            hn_signals = f_hn.result(timeout=6)
        except Exception:
            hn_signals = []

    context["liveJobs"] = adzuna_jobs + remote_jobs
    context["trendingTechnologies"] = trending
    context["marketArticles"] = news
    context["hiringSignals"] = hn_signals
    
    now = datetime.now().isoformat()
    context["dataFreshness"]["jobs_fetched_at"] = now if context["liveJobs"] else "unavailable"
    context["dataFreshness"]["articles_fetched_at"] = now if context["marketArticles"] else "unavailable"
    context["dataFreshness"]["trending_fetched_at"] = now if context["trendingTechnologies"] else "unavailable"
    
    return context
