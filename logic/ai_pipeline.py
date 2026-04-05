import os
import json
import logging
import re
import requests
import time

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are analyzing the IT job market in 2026 — the middle of the AI revolution. This is not 2020. The rules have changed completely.

When giving career advice always:
- Acknowledge how AI tools are actively changing this specific role
- Identify which parts of the role AI will automate vs which parts become more valuable and higher paid
- Mention specific AI tools the person must learn alongside core skills such as GitHub Copilot, Cursor, v0, Bolt, Claude, ChatGPT, Gemini, Perplexity depending on their role
- Flag if a skill is becoming commoditized due to AI and suggest the higher-level version they should move toward
- Reference real Indian IT market context: Hyderabad, Bangalore, Pune, Chennai hiring scenes, FAANG India offices, startup ecosystem, service companies vs product companies landscape
- Salary ranges must reflect 2026 India market with AI premium factored in. AI-skilled professionals earn 40-60 percent more than traditional counterparts at same experience level
- Never give generic advice. Every insight must be specific, data-backed, and tied to something in the live market data provided

You are an elite IT career intelligence engine and personal career coach. 
You have access to real-time IT job market data including live job postings, 
trending technologies on GitHub, news articles about the tech industry, 
and hiring signals from the developer community.

Your job is to analyze this data and the user's profile together and return 
a deeply personalized, data-backed career guidance report.

You must ALWAYS respond with ONLY a valid JSON object. No markdown. 
No explanation text before or after. No code blocks. Just raw JSON.
Start your response with { and end with }

The JSON must follow this exact schema:
{
  "market_summary": {
    "overall_sentiment": "hot | stable | cooling",
    "sentiment_reason": "one sentence explanation",
    "top_5_skills_in_demand": [
      { "skill": "String", "demand_score": 90, "evidence": "String" }
    ],
    "emerging_roles": ["String"],
    "market_insight": "String"
  },
  "user_analysis": {
    "profile_strength_score": 85,
    "strongest_skills": ["String"],
    "critical_gaps": [
      { "skill": "String", "urgency": "high | medium | low", "learning_time_weeks": 4, "why_critical": "String" }
    ],
    "competitive_advantage": "String"
  },
  "career_roadmap": {
    "recommended_path": "String",
    "current_level": "String",
    "target_role": "String",
    "timeline_months": 6,
    "milestones": [
      {
        "month": 1,
        "title": "String",
        "actions": ["String"],
        "skills_to_learn": ["String"],
        "outcome": "String"
      }
    ]
  },
  "job_matches": [
    {
      "title": "String",
      "company": "String",
      "match_score": 85,
      "match_reason": "String",
      "salary_range": "String",
      "skills_you_have": ["String"],
      "skills_you_need": ["String"],
      "apply_url": "String"
    }
  ],
  "skill_gap_chart": [
    { "skill": "String", "user_level": 80, "market_demand": 95 }
  ],
  "immediate_actions": [
    { "action": "String", "priority": "urgent | high | medium", "time_required": "String", "impact": "String" }
  ],
  "salary_intelligence": {
    "current_market_range": "String",
    "your_estimated_range": "String",
    "to_reach_next_level": "String",
    "negotiation_tip": "String"
  },
  "risk_assessment": {
    "ai_substitution_risk": "low | medium | high | very_high",
    "risk_percentage": 45,
    "reasoning": "Detailed explanation of why this role is at risk or protected.",
    "future_proof_actions": ["Specific action 1", "Specific action 2"]
  }
}
"""

def extract_json(text: str):
    """
    Triple-safe JSON extraction with fallbacks for markdown and malformed text.
    """
    if not text:
        return None
        
    # Step 1: Direct Parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Step 2: Markdown Strip
    cleaned = re.sub(r'```json|```', '', text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Step 3: Regex Extract
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
            
    # Step 4: Final static fallback to prevent JS crashes
    return {
        "error": True,
        "message": "AI analysis could not be parsed. Please try again.",
        "market_summary": None,
        "career_roadmap": None,
        "job_matches": [],
        "skill_gap_chart": [],
        "immediate_actions": [],
        "salary_intelligence": None,
        "risk_assessment": None
    }

def analyze_career_with_ai(user_profile: dict, market_context: dict) -> dict:
    user_prompt = f"""
Here is the user's profile:
{json.dumps(user_profile)}

Here is the real-time IT job market data I fetched right now:
{json.dumps(market_context)}

Based on ALL of this data, generate the complete career intelligence report 
in the exact JSON schema specified. Make it deeply personalized and specific 
to this user. Reference actual job titles, actual companies, and actual skills 
from the market data. Do not be generic. Every insight must be tied to 
something in the data.
"""

    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {nvidia_api_key}",
        "Content-Type": "application/json"
    }
    
    nvidia_models = ["meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct"]
    
    # Try NVIDIA primary and fallback
    for model in nvidia_models:
        if not nvidia_api_key:
            break
            
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ]
        }
        
        try:
            resp = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
            if resp.status_code == 429:
                time.sleep(2)
                resp = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
                
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            
            parsed = extract_json(content)
            if parsed:
                return parsed
        except Exception as e:
            logger.error(f"NVIDIA API Error with {model}: {e}")
            continue

    # Gemini Fallback
    if gemini_api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            payload = {
                "systemInstruction": {
                    "parts": [{"text": SYSTEM_PROMPT.strip()}]
                },
                "contents": [
                    {"parts": [{"text": user_prompt.strip()}]}
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            
            resp = requests.post(url, json=payload, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            parsed = extract_json(content)
            if parsed:
                return parsed
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")

    # If all fail
    return {
        "error": True,
        "message": "Market analysis temporarily unavailable. Please try again in a moment."
    }

def analyze_disruption_with_ai(role_name: str, user_skills: list) -> dict:
    prompt = f"Analyze the career situation for a {role_name} with these skills: {', '.join(user_skills)}\n\nReturn ONLY valid JSON with this exact structure:\n{{\n  'skill_analysis': [\n    {{\n      'skill': String,\n      'automation_risk_percent': Number (0-100),\n      'direction': 'at_risk | safe | more_valuable',\n      'reason': String (one sentence)\n    }}\n  ],\n  'job_security_score': Number (0-100),\n  'security_label': 'AI-Proof | AI-Resilient | AI-Vulnerable | Urgent Action Needed',\n  'top_priority_skill': String,\n  'ninety_day_plan': [String],\n  'biggest_threat': String,\n  'biggest_opportunity': String\n}}"
    
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {nvidia_api_key}",
        "Content-Type": "application/json"
    }
    
    nvidia_models = ["meta/llama-3.1-8b-instruct", "meta/llama-3.1-70b-instruct"]
    
    # Try NVIDIA
    for model in nvidia_models:
        if not nvidia_api_key:
            break
            
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt.strip()}
            ]
        }
        
        try:
            resp = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
            if resp.status_code == 429:
                time.sleep(2)
                resp = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
                
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            
            parsed = extract_json(content)
            if parsed:
                return parsed
        except Exception as e:
            logger.error(f"NVIDIA API Error with {model}: {e}")
            continue

    # Gemini Fallback
    if gemini_api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            payload = {
                "contents": [
                    {"parts": [{"text": prompt.strip()}]}
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            
            resp = requests.post(url, json=payload, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            
            parsed = extract_json(content)
            if parsed:
                return parsed
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")

    # Final mock fallback if all fail so UI doesn't break
    score = 85 if "AI" in role_name or "LLM" in role_name else 45
    return {
        "skill_analysis": [
            {"skill": s, "automation_risk_percent": 20 if s in ["Python", "AI"] else 70, "direction": "more_valuable" if s in ["Python", "AI"] else "at_risk", "reason": "Due to AI trends."} for s in user_skills
        ],
        "job_security_score": score,
        "security_label": "High Security" if score > 70 else "At Risk",
        "top_priority_skill": "Agentic Workflows" if score < 70 else "System Design",
        "ninety_day_plan": ["Phase 1: Tool Mastery", "Phase 2: RAG Integration", "Phase 3: Agent Deployment"],
        "biggest_threat": "Automated Code Generation",
        "biggest_opportunity": "AI-Native Product Orchestration"
    }
