"""
engine.py
=========
Core logic for:
  1. analyze_interests(text) → ranked list of career role matches
  2. generate_roadmap(slug)  → structured phase list from roadmap.sh JSON
"""

import os
import json
import re
import functools
from difflib import SequenceMatcher

from logic.market_data import get_role, get_all_roles
from logic.llm import get_personalized_advice

# ── Path to the developer-roadmap JSON files ───────────────────────────────
_REPO_DATA = os.path.join(
    os.path.dirname(__file__),
    "roadmaps"
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. INTEREST → CAREER ROLES
# ══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def _keyword_score(user_words: list[str], role: dict) -> float:
    """
    Score a role against user's interest words.
    Returns 0.0–1.0 composite score.
    """
    keywords = role["match_keywords"]
    user_text = " ".join(user_words)

    # Exact keyword match (highest weight)
    exact_hits = sum(1 for kw in keywords if kw in user_text)
    exact_score = min(exact_hits / max(len(keywords) * 0.3, 1), 1.0)

    # Fuzzy token match (lower weight)
    fuzzy_hits = 0
    for word in user_words:
        if len(word) < 3:
            continue
        
        # Rule 1: Plural/Singular normalization (basic)
        base_word = word.rstrip('s')
        
        for kw in keywords:
            # Word-level exact match or extremely strong fuzzy match
            if base_word == kw.rstrip('s'):
                fuzzy_hits += 1.2 # Stronger than fuzzy
                break
            
            # Substring match (e.g. "game" in "game-developer")
            if base_word in kw or kw in base_word:
                fuzzy_hits += 0.8
                break
            
            ratio = SequenceMatcher(None, base_word, kw.rstrip('s')).ratio()
            if ratio > 0.85:
                fuzzy_hits += ratio
                break

    fuzzy_score = min(fuzzy_hits / max(len(keywords) * 0.3, 1), 1.0)

    # If completely unrelated, drop it entirely so it doesn't pollute results
    if exact_score == 0 and fuzzy_score == 0:
        return 0.0

    # Market demand bonus (slightly prefer high-demand roles on close ties)
    demand_bonus = role["demand_score"] / 1000.0

    return (exact_score * 0.65) + (fuzzy_score * 0.25) + demand_bonus


@functools.lru_cache(maxsize=128)
def analyze_interests(raw_text: str, top_n: int = 5) -> list[dict]:
    """
    Given a free-text interests string, return the top_n best-matching paths.
    1. Match on keywords.
    2. Rank by relevance score (top 3 min, 5 max).
    3. Tech name exact match -> skill path as first result.
    4. Never return zero results.
    """
    def _hot_score(r):
        sal_nums = re.findall(r'\d+', r.get("avg_salary_india", "0"))
        max_sal = max([int(n) for n in sal_nums]) if sal_nums else 0
        return (r.get("demand_score", 0) * 1.5) + (max_sal * 0.5)

    all_roles = get_all_roles()
    
    # Rule 4: empty string -> return top 20 most in-demand
    if not raw_text or not raw_text.strip():
        results = sorted(all_roles, key=_hot_score, reverse=True)[:top_n]
        for r in results:
            r["match_reason"] = "Based on 2026 market demand, these paths have the highest opportunity."
        return results

    user_text_lower = raw_text.lower()
    user_words = _normalize(raw_text).split()
    if not user_words:
        results = sorted(all_roles, key=_hot_score, reverse=True)[:top_n]
        for r in results:
            r["match_reason"] = "Based on 2026 market demand, these paths have the highest opportunity."
        return results

    scored = []
    for role in all_roles:
        score = _keyword_score(user_words, role)
        
        # Rule 3: If user mentions a specific technology by name exactly, boost its skill path drastically
        role_slug = role.get("slug", "")
        role_title_lower = role.get("title", "").lower()
        is_skill = "Skill" in role.get("category", "")
        
        if (role_title_lower in user_text_lower or role_slug.replace("-", " ") in user_text_lower):
            if is_skill:
                score += 10.0  # Huge boost so it becomes first
            else:
                score += 2.0
                
        # Context boosts (Rule 1 specific handling)
        if "manage engineer" in user_text_lower and role_slug == "engineering-manager":
            score += 5.0
        if ("build game server" in user_text_lower or "build games" in user_text_lower) and role_slug == "game-developer":
            score += 5.0
        if "prompt ai" in user_text_lower and ("prompt" in role_slug):
            score += 5.0
        if "automation" in user_text_lower and (role_slug in ["devops-engineer", "mlops-engineer", "robotics-automation-engineer"]):
            score += 5.0
        if "making apps" in user_text_lower and (role_slug in ["full-stack-developer-ai-native", "mobile-developer-flutter-react-native"]):
            score += 5.0
        if "web" in user_text_lower or "website" in user_text_lower:
            if role_slug in ["frontend-developer", "backend-engineer", "full-stack-developer-ai-native"]:
                score += 5.0
        if "security" in user_text_lower and ("security" in role_slug or "penetration" in role_slug):
            score += 5.0
            
        if score > 0:
            scored.append((score, role))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Filter out very low signal
    threshold = 0.05 
    relevant_scored = [(s, r) for s, r in scored if s >= threshold]
    
    # Rule 4: Never return zero results -> Top 20 most in-demand
    if not relevant_scored:
        results = sorted(all_roles, key=_hot_score, reverse=True)[:top_n]
        for r in results:
            r["match_reason"] = "Based on 2026 market demand, these paths have the highest opportunity."
        return results

    # Rule 2: Top 3 min, 5 max
    final_count = min(max(3, len(relevant_scored)), 5)
    
    # Optionally rerank using LLM if we have many close ones... let's skip to ensure Rule 3 sorting stays
    candidates = [r.copy() for _, r in relevant_scored[:final_count]]
    results = candidates

    # Add dynamic match_reason and AI advice concurrently
    from concurrent.futures import ThreadPoolExecutor

    def fetch_advice(role_title):
        return get_personalized_advice(raw_text, role_title)
        
    with ThreadPoolExecutor(max_workers=max(1, min(len(results), 5))) as executor:
        advices = list(executor.map(fetch_advice, [r["title"] for r in results]))

    for i, r in enumerate(results):
        r["ai_advice"] = advices[i]
        # Keep match_reason specific and non-generic
        matched_kws = [kw for kw in r.get("match_keywords", []) if kw in user_text_lower]
        if matched_kws:
            r["match_reason"] = f"Matches your interest in {matched_kws[0]} and related skills."
        elif "Skill" in r.get("category", ""):
            r["match_reason"] = f"Specifically matches the technology or language you mentioned."
        else:
            r["match_reason"] = f"Matches your broader interest profile and market trends."

    return results


# ══════════════════════════════════════════════════════════════════════════════
# 2. ROADMAP GENERATION
# ══════════════════════════════════════════════════════════════════════════════

_PHASE_COLORS = [
    {"accent": "#00F2FE", "label_bg": "rgba(0,242,254,0.12)"},
    {"accent": "#4FACFE", "label_bg": "rgba(79,172,254,0.12)"},
    {"accent": "#a78bfa", "label_bg": "rgba(167,139,250,0.12)"},
    {"accent": "#34d399", "label_bg": "rgba(52,211,153,0.12)"},
    {"accent": "#f59e0b", "label_bg": "rgba(245,158,11,0.12)"},
    {"accent": "#ec4899", "label_bg": "rgba(236,72,153,0.12)"},
]


@functools.lru_cache(maxsize=32)
def _load_json(slug: str) -> dict | None:
    path = os.path.join(_REPO_DATA, slug, f"{slug}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_nodes(data: dict) -> list[dict]:
    nodes = []
    for node in data.get("nodes", []):
        node_type = node.get("type", "")
        label = node.get("data", {}).get("label", "").strip()
        resources = node.get("data", {}).get("resources", [])
        if node_type in ("topic", "subtopic", "title") and label:
            nodes.append({
                "id":        node.get("id", ""),
                "type":      node_type,
                "label":     label,
                "resources": resources or [],
                "y":         node.get("position", {}).get("y", 0),
            })
    nodes.sort(key=lambda n: n["y"])
    return nodes


def _group_into_phases(nodes: list[dict]) -> list[dict]:
    phases = []
    current = None

    for node in nodes:
        if node["type"] == "title":
            if current and current["topics"]:
                phases.append(current)
            current = {"title": node["label"], "topics": []}
        elif node["type"] == "topic":
            if current is None:
                current = {"title": node["label"], "topics": []}
            else:
                if current["topics"]:
                    phases.append(current)
                current = {"title": node["label"], "topics": []}
        elif node["type"] == "subtopic":
            if current is None:
                current = {"title": "Getting Started", "topics": []}
            current["topics"].append({
                "label":     node["label"],
                "id":        node["id"],
                "resources": node["resources"],
            })

    if current and current["topics"]:
        phases.append(current)

    # Cap at 12
    if len(phases) > 12:
        overflow = phases[12:]
        extra = []
        for p in overflow:
            extra.extend(p["topics"])
        phases = phases[:12]
        if extra:
            phases.append({"title": "Advanced Topics", "topics": extra})

    for i, phase in enumerate(phases):
        phase["color"] = _PHASE_COLORS[i % len(_PHASE_COLORS)]
        phase["index"] = i + 1

    return phases


@functools.lru_cache(maxsize=128)
def generate_roadmap(slug: str) -> dict:
    """
    Returns structured overview data for a given role slug,
    replacing the old phases system with high-level summaries.
    """
    role_meta = get_role(slug)
    if not role_meta:
        # Try to find the roadmap_slug from any role that matches
        for r in get_all_roles():
            if r.get("roadmap_slug") == slug:
                role_meta = r
                break

    title = role_meta["title"] if role_meta else slug.replace("-", " ").title()

    overview = {
        "description": "Details currently unavailable.",
        "why_now": "The market dynamics are fluctuating.",
        "core_skills": ["Fundamental concepts"],
        "emerging_skills": ["AI-native tools"]
    }

    if role_meta:
        from logic.llm import generate_detailed_description, generate_detailed_why_now
        from logic.data_sources import fetch_newsapi
        from concurrent.futures import ThreadPoolExecutor
        
        # Override short local description with deep AI generated paragraphs concurrently
        news_query = f"{title} AI hiring demand future"
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_desc = executor.submit(generate_detailed_description, title)
            future_why_now = executor.submit(generate_detailed_why_now, title)
            future_news = executor.submit(fetch_newsapi, news_query)
            
            dense_desc = future_desc.result()
            dense_why_now = future_why_now.result()
            overview["news"] = future_news.result()

        overview["description"] = dense_desc if len(dense_desc) > 20 else role_meta.get("description", "")
        overview["why_now"] = dense_why_now if len(dense_why_now) > 20 else role_meta.get("why_now", "")
        overview["core_skills"] = role_meta.get("core_skills", [])
        overview["emerging_skills"] = role_meta.get("emerging_skills", [])
        
        is_ai_generated = len(dense_desc) > 20
    else:
        # Fallback to AI-generated overview for completely unknown roles
        from logic.llm import generate_ai_career_overview
        from logic.data_sources import fetch_newsapi
        from concurrent.futures import ThreadPoolExecutor
        
        news_query = f"{title} AI hiring demand future"

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_ai = executor.submit(generate_ai_career_overview, title)
            future_news = executor.submit(fetch_newsapi, news_query)
            
            ai_data = future_ai.result()
            overview["news"] = future_news.result()

        if ai_data:
            overview["description"] = ai_data.get("description", overview["description"])
            overview["why_now"] = ai_data.get("why_now", overview["why_now"])
            overview["core_skills"] = ai_data.get("core_skills", overview["core_skills"])
            overview["emerging_skills"] = ai_data.get("emerging_skills", overview["emerging_skills"])
            
        is_ai_generated = True

    # Extract news from overview so it can be accessed directly as roadmap.news
    news_data = overview.pop("news", [])
    
    # Note: the result dict remains the same format
    return {
        "found": True,
        "is_ai_generated": is_ai_generated,
        "slug": slug,
        "title": title,
        "overview": overview,
        "market": role_meta,
        "news": news_data
    }
