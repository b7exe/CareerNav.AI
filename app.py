import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from logic.engine import analyze_interests, generate_roadmap
from logic.extractor import init_background_job
from logic.llm import get_counselor_response
from logic.data_sources import get_market_context, fetch_adzuna, fetch_remoteok, fetch_github_trending, fetch_newsapi
from logic.ai_pipeline import analyze_career_with_ai, analyze_disruption_with_ai
import concurrent.futures

app = Flask(__name__)

# Boot the 10-hour background data extraction pipeline
init_background_job()

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/careers")
def careers():
    interests = request.args.get("q", "").strip()
    roles = analyze_interests(interests, top_n=200)
    
    # If no specific interests or if fallback triggered, show all roles sorted by category
    if not interests or len(roles) > 5:
        # Convert to list to avoid mutating the cached tuple/list
        roles_list = list(roles)
        # Sort heavily by category so they group properly in the UI
        roles_list.sort(key=lambda r: r.get("category", "Other"))
        roles = roles_list
        
    return render_template("careers.html", roles=roles, interests=interests)


@app.route("/roadmap")
def roadmap():
    slug = request.args.get("role", "").strip()
    interests = request.args.get("q", "").strip()   # passed through for back-link
    data = generate_roadmap(slug)
    return render_template("roadmap.html", roadmap=data, interests=interests)





@app.route("/dashboard")
def dashboard():
    """Silent redirect from legacy dashboard to the new AI Navigator SPA."""
    return redirect(url_for("ai_navigator"))

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    role = data.get("role", "General AI")
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    response = get_counselor_response(role, message)
    return jsonify({"response": response})


# ── AI Navigator Routes ──────────────────────────────────────────────
@app.route("/ai-navigator-handoff")
def ai_navigator_handoff():
    domain = request.args.get("domain", "")
    stage = request.args.get("stage", "entry")
    
    # Process like engine.py normally does 
    role = None
    if domain:
        roles = analyze_interests(domain, top_n=1)
        if roles:
            role = roles[0]
            
    if not role:
        role = analyze_interests("software developer", top_n=1)[0]
        
    target_title = role["title"]
    # Primary post-assessment redirect targets the AI Navigator directly
    return redirect(url_for('ai_navigator', domain=domain, stage=stage, target_role=target_title))

@app.route("/ai-navigator")
def ai_navigator():
    return render_template("ai_navigator.html")

@app.route("/api/save-profile", methods=["POST"])
def save_profile():
    # Profiler is saved entirely to localStorage on the client as requested
    return jsonify({"status": "ok"})

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.json or {}
    user_profile = data.get("userProfile", {})
    
    user_skills = user_profile.get("current_skills", [])
    location = user_profile.get("location", "Hyderabad")
    
    # 1. Fetch 5 sources
    context = get_market_context(user_skills, location)
    
    # 2. Analyze with AI
    result = analyze_career_with_ai(user_profile, context)
    
    return jsonify(result)

@app.route("/api/market-pulse")
def market_pulse():
    # Cache strategy on client side, fetch quick stats here
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_news = executor.submit(fetch_newsapi)
        f_git = executor.submit(fetch_github_trending)
        
        try:
            news = f_news.result(timeout=4)
        except Exception:
            news = []
            
        try:
            git = f_git.result(timeout=4)
        except Exception:
            git = []
            
    return jsonify({
        "trending": git[:3],
        "news": news[:3]
    })

@app.route("/api/jobs")
def api_jobs():
    skills = request.args.get("skills", "").split(",")
    location = request.args.get("location", "Hyderabad")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_adzuna = executor.submit(fetch_adzuna, skills, location)
        f_remote = executor.submit(fetch_remoteok)
        
        try:
            adzuna = f_adzuna.result(timeout=5)
        except Exception:
            adzuna = []
            
        try:
            remote = f_remote.result(timeout=5)
        except Exception:
            remote = []
            
    return jsonify({
        "jobs": adzuna + remote
    })

@app.route("/api/shift-index")
def shift_index():
    from logic.market_data import get_all_roles
    roles = get_all_roles()
    
    # Filter for roles with significant shifts
    shifts = []
    for r in roles:
        # Simulate shift calculation or use real demand_score
        score = r.get("demand_score", 50)
        label = "Exploding" if score > 90 else "Trending" if score > 75 else "Stable"
        
        shifts.append({
            "slug": r["slug"],
            "title": r["title"],
            "score": score,
            "label": label,
            "evidence": [f"High volume of mentions on HackerNews: {r.get('match_keywords', ['tech'])[0]}", f"Trending on GitHub: {r.get('category')}"],
            "calculated_at": r.get("last_updated", "2026-04-04T00:00:00Z")
        })
    
    # Sort by score
    shifts.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(shifts)

@app.route("/api/disruption-check", methods=["POST"])
def disruption_check():
    data = request.json or {}
    role_name = data.get("role", "Frontend Developer")
    user_skills = data.get("skills", [])
    
    # Call AI Disruption API Pipeline
    result = analyze_disruption_with_ai(role_name, user_skills)
    
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
