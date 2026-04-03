"""
market_data.py
==============
Curated career intelligence dataset with brutally realistic 2026 recalibration.

Sources simulated from:
- roadmap.sh community data (skills, paths)
- BLS & LinkedIn Workforce Reports (demand, salaries)
- Reddit/X tech hiring trends & layoffs tracking
- Future Risk Analysis for AI substitution (High penalties for boilerplate tech)

Includes orthodox tech paths and 2026+ hybrid AI domains.
"""
import os
import json

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'market_cache.json')

DEFAULT_ROLES = {
    # ── AI / ML ─────────────────────────────────────────────────────────
    "ai-engineer": {
        "slug": "ai-engineer",
        "title": "AI Engineer",
        "demand_score": 94,
        "yoy_growth": "+45%",
        "avg_salary": "$145k – $210k",
        "scope": "Explosive",
        "lifetime": "Medium-term (5-8 yrs)",
        "risk_level": "Growing Risk (Market Saturation & AutoML)",
        "trending": True,
        "trending_reason": "High demand, but fierce competition. Wrappers are dead, deep integration is baseline.",
        "social_signal": 92,
        "top_hiring": ["OpenAI", "Anthropic", "Google", "Microsoft"],
        "tag": "High Demand",
        "roadmap_slug": "ai-engineer",
        "match_keywords": ["ai", "artificial intelligence", "llm", "gpt", "openai", "generative", "ml", "language model", "build ai"]
    },
    "machine-learning": {
        "slug": "machine-learning",
        "title": "Machine Learning Engineer",
        "demand_score": 88,
        "yoy_growth": "+22%",
        "avg_salary": "$135k – $200k",
        "scope": "High",
        "lifetime": "Long-term (10+ yrs)",
        "risk_level": "Moderate Risk (Model training is centralizing to giants)",
        "trending": False,
        "trending_reason": "Training foundation models is too expensive for 99% of companies. Focus is shifting to inference.",
        "social_signal": 85,
        "top_hiring": ["Google", "Meta", "Nvidia", "Hugging Face"],
        "tag": "Stabilizing",
        "roadmap_slug": "machine-learning",
        "match_keywords": ["machine learning", "ml", "data", "models", "training", "tensorflow", "pytorch", "algorithms", "math"]
    },
    "mlops": {
        "slug": "mlops",
        "title": "MLOps Engineer",
        "demand_score": 92,
        "yoy_growth": "+35%",
        "avg_salary": "$130k – $195k",
        "scope": "Very High",
        "lifetime": "Long-term (8+ yrs)",
        "risk_level": "Low Risk (Infrastructure moat)",
        "trending": True,
        "trending_reason": "AI models are useless if they don't scale. Hard physical infra problems defeat code-gen bots.",
        "social_signal": 85,
        "top_hiring": ["Databricks", "Scale AI", "AWS", "Snowflake"],
        "tag": "Critical infra",
        "roadmap_slug": "mlops",
        "match_keywords": ["mlops", "devops ml", "model deployment", "kubernetes ml", "infrastructure", "docker", "deploy models"]
    },
    "ai-data-scientist": {
        "slug": "ai-data-scientist",
        "title": "Data Scientist",
        "demand_score": 58,
        "yoy_growth": "-8%",
        "avg_salary": "$110k – $160k",
        "scope": "Declining",
        "lifetime": "Short-term (Vulnerable)",
        "risk_level": "High Risk (Auto-analytics and Code-Interpreter taking over)",
        "trending": False,
        "trending_reason": "ChatGPT Data Analyst tools can do 80% of junior data science work instantly.",
        "social_signal": 60,
        "top_hiring": ["Palantir", "JPMorgan", "Stripe"],
        "tag": "At Risk",
        "roadmap_slug": "ai-data-scientist",
        "match_keywords": ["data science", "data scientist", "analytics", "statistics", "jupyter", "pandas", "numpy", "research"]
    },
    # ── Web Development (BRUTAL RECALS) ──────────────────────────────────
    "frontend": {
        "slug": "frontend",
        "title": "Frontend Developer",
        "demand_score": 45,
        "yoy_growth": "-15%",
        "avg_salary": "$85k – $135k",
        "scope": "Saturating",
        "lifetime": "Short-term",
        "risk_level": "Extremely High (AI UI Code-generation is flawless)",
        "trending": False,
        "trending_reason": "Tools like v0 and Claude Artifacts write production UI in seconds. Junior roles are evaporating.",
        "social_signal": 50,
        "top_hiring": ["Agency work", "Legacy tech upgrades", "Shopify"],
        "tag": "Saturated",
        "roadmap_slug": "frontend",
        "match_keywords": ["frontend", "web", "html", "css", "react", "vue", "javascript", "ui", "browser", "websites"]
    },
    "backend": {
        "slug": "backend",
        "title": "Backend Developer",
        "demand_score": 70,
        "yoy_growth": "-2%",
        "avg_salary": "$100k – $155k",
        "scope": "Moderate",
        "lifetime": "Medium-term",
        "risk_level": "High Risk (Standard CRUD APIs are easily botted)",
        "trending": False,
        "trending_reason": "Standard API development is accelerating via AI. You must pivot to distributed systems.",
        "social_signal": 68,
        "top_hiring": ["Cloudflare", "Stripe", "AWS", "Financial sector"],
        "tag": "Commoditized",
        "roadmap_slug": "backend",
        "match_keywords": ["backend", "server", "api", "database", "node", "python", "java", "sql", "rest", "microservices"]
    },
    "full-stack": {
        "slug": "full-stack",
        "title": "Full Stack / Product Engineer",
        "demand_score": 82,
        "yoy_growth": "+12%",
        "avg_salary": "$115k – $180k",
        "scope": "High",
        "lifetime": "Medium-term",
        "risk_level": "Moderate Risk (Needs strong domain logic)",
        "trending": True,
        "trending_reason": "AI gives generalists superpowers. Solo 10x developers are real, replacing segmented teams.",
        "social_signal": 86,
        "top_hiring": ["Startups", "Y Combinator", "Vercel", "Linear"],
        "tag": "10x Generalist",
        "roadmap_slug": "full-stack",
        "match_keywords": ["full stack", "fullstack", "both frontend backend", "startup", "product", "build things", "saas"]
    },
    # ── Infrastructure / DevOps / Security ──────────────────────────────
    "devops": {
        "slug": "devops",
        "title": "DevOps / Platform Engineer",
        "demand_score": 95,
        "yoy_growth": "+32%",
        "avg_salary": "$130k – $190k",
        "scope": "Very High",
        "lifetime": "Long-term (10+ yrs)",
        "risk_level": "Very Low Risk (Untouchable physical infra)",
        "trending": True,
        "trending_reason": "AI cannot securely debug live cloud outages or rack hardware. Physical world moat is massive.",
        "social_signal": 88,
        "top_hiring": ["AWS", "HashiCorp", "Datadog", "PagerDuty"],
        "tag": "Safe Haven",
        "roadmap_slug": "devops",
        "match_keywords": ["devops", "infrastructure", "cloud", "aws", "kubernetes", "ci/cd", "deployment", "terraform"]
    },
    "cyber-security": {
        "slug": "cyber-security",
        "title": "Cybersecurity Engineer",
        "demand_score": 98,
        "yoy_growth": "+45%",
        "avg_salary": "$135k – $200k",
        "scope": "Explosive",
        "lifetime": "Long-term (Defensive)",
        "risk_level": "Negative Risk (AI increases the threat surface)",
        "trending": True,
        "trending_reason": "AI-powered malware means humans are needed for extreme defense. Massive global deficit of sec engineers.",
        "social_signal": 95,
        "top_hiring": ["CrowdStrike", "Palo Alto Networks", "NSA", "Defense Contractors"],
        "tag": "Critical Shortage",
        "roadmap_slug": "cyber-security",
        "match_keywords": ["security", "cybersecurity", "hacking", "penetration", "red team", "soc", "malware", "vulnerabilities"]
    },
    "ai-red-teaming": {
        "slug": "ai-red-teaming",
        "title": "AI Red Team Engineer",
        "demand_score": 96,
        "yoy_growth": "+110%",
        "avg_salary": "$150k – $220k",
        "scope": "Explosive",
        "lifetime": "Long-term",
        "risk_level": "Low Risk",
        "trending": True,
        "trending_reason": "Governments and mega-corps are terrified of rogue LLMs. Red teaming compliance is legally scaling.",
        "social_signal": 96,
        "top_hiring": ["Anthropic", "OpenAI", "NIST", "Scale AI"],
        "tag": "Regulatory Gold",
        "roadmap_slug": "ai-red-teaming",
        "match_keywords": ["ai safety", "red team", "llm security", "prompt injection", "jailbreak", "bias", "alignment"]
    },
    # ── Prompt Engineering ─────────────────────────────────────────────
    "prompt-engineering": {
        "slug": "prompt-engineering",
        "title": "Prompt Engineer",
        "demand_score": 25,
        "yoy_growth": "-60%",
        "avg_salary": "$70k – $110k",
        "scope": "Crashing",
        "lifetime": "Dead End",
        "risk_level": "Total Obsolescence (Now a basic required skill, not a job)",
        "trending": False,
        "trending_reason": "The hype bubble popped. Models now optimize their own prompts (DSPy, o1 reasoning). Do not pursue as a career.",
        "social_signal": 35,
        "top_hiring": ["Nobody", "Low-tier SEO farms"],
        "tag": "Obsolete Bubble",
        "roadmap_slug": "prompt-engineering",
        "match_keywords": ["prompt", "prompt engineering", "chatgpt", "claude", "no code", "ai tools", "productivity"]
    },
    # ── Mobile ──────────────────────────────────────────────────────────
    "android": {
        "slug": "android",
        "title": "Android Developer",
        "demand_score": 55,
        "yoy_growth": "-5%",
        "avg_salary": "$100k – $150k",
        "scope": "Stagnant",
        "lifetime": "Medium-term",
        "risk_level": "High Risk (Cross-platform and AI generation)",
        "trending": False,
        "trending_reason": "Native mobile development is slowing. React Native/Flutter take majority, AI handles the rest.",
        "social_signal": 60,
        "top_hiring": ["Enterprise tech", "Legacy codebases"],
        "tag": "Declining",
        "roadmap_slug": "android",
        "match_keywords": ["android", "mobile", "kotlin", "java android", "app development", "play store"]
    },
    # ── System Design ────────────────────────────────────────────────────
    "system-design": {
        "slug": "system-design",
        "title": "Software Architect",
        "demand_score": 92,
        "yoy_growth": "+15%",
        "avg_salary": "$160k – $250k",
        "scope": "Very High",
        "lifetime": "Long-term",
        "risk_level": "Very Low Risk (Strategy & Context > Code Generation)",
        "trending": True,
        "trending_reason": "AI writes functions, architects build systems. The bottleneck is orchestrating large-scale context.",
        "social_signal": 88,
        "top_hiring": ["FAANG", "Financials", "Unicorns"],
        "tag": "High Leverage",
        "roadmap_slug": "system-design",
        "match_keywords": ["architecture", "system design", "distributed systems", "scalability", "senior engineer", "principal"]
    },
}

def _get_active_roles() -> dict:
    """Read from the live background cache, fallback to DEFAULT_ROLES if missing."""
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
