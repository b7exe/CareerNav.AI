import os
import json
import logging
from typing import Optional, List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (API key)
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure NVIDIA (OpenAI-compatible)
API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"

if API_KEY:
    try:
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=API_KEY
        )
        logger.info(f"NVIDIA API client initialized with model: {MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize NVIDIA client: {e}")
        client = None
else:
    logger.warning("NVIDIA_API_KEY not found in .env. AI features will be disabled.")
    client = None

def get_personalized_advice(interests: str, role_title: str) -> str:
    """
    Generates a short, brutally realistic 'Counselor's Take' on why a role matches a user's interests.
    """
    if not client or not interests:
        return "Connect your interests to see personalized AI career reasoning."

    prompt = f"""
    You are a brutally realistic AI Career Counselor in the year 2026. 
    A user with these interests: "{interests}"
    is being matched with the role: "{role_title}".

    TASK:
    1. Explain WHY this career path is a strong (or risky) match for their interests.
    2. Be specific. Connect their interest words to the role's requirements.
    3. Use a high-tech, slightly cynical, but insightful tone.
    4. Keep it to exactly 2 sentences.
    
    Output Format:
    'Why this match? [Your 2-sentence explanation]'
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        text = completion.choices[0].message.content.strip()
        if text.startswith("Why this match?"):
            return text
        return f"Why this match? {text}"
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        return "The AI counselor is currently offline. Market volatility is high."

def generate_ai_roadmap(role_title: str) -> Optional[Dict]:
    """
    Generates a structured roadmap JSON if local data is missing.
    """
    if not client:
        return None

    prompt = f"""
    Generate a career roadmap for the role: "{role_title}".
    Structure it as a series of PHASES. Each phase should have a 'title' and a list of 'topics'.
    Return ONLY a valid JSON object with a 'phases' key.
    
    Format example:
    {{
      "phases": [
        {{ "title": "Phase 1: Fundamentals", "topics": ["Topic A", "Topic B"] }},
        {{ "title": "Phase 2: Advanced", "topics": ["Topic C"] }}
      ]
    }}
    
    Be brutally realistic for the year 2026. Include AI tools and hybrid skills.
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error generating AI roadmap: {e}")
        return None

def get_counselor_response(role_title: str, user_question: str) -> str:
    """
    Simulates a chat with a specific career counselor for a role.
    """
    if not client:
        return "I'm busy tracking market crashes. Set up an API key to talk."

    prompt = f"""
    You are an expert Career Counselor specializing in {role_title}. 
    The year is 2026. The market is volatile, AI is everywhere, and only the elite survive.
    The user asks: "{user_question}".
    
    Answer as the {role_title} counselor. Be concise, insightful, and brutally honest. 
    Use a professional but high-tech tone.
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating counselor response: {e}")
        return "System error. My neural links are fried."

def rerank_roles(interests: str, roles: List[Dict]) -> List[Dict]:
    """
    Uses the LLM to pick the best matches from a list of candidates.
    Ensures that "Android Developer" won't show up for "Hacking and AI".
    """
    if not client or not roles:
        return roles

    role_list_str = "\n".join([f"- {r['slug']}: {r['title']}" for r in roles])
    
    prompt = f"""
    A user has these interests: "{interests}".
    
    Which of these career roles are GENUINELY relevant? 
    Exclude any that are only loose or technical keyword matches but don't fit the core theme.
    
    CANDIDATES:
    {role_list_str}
    
    Return ONLY a JSON array of the slugs in ranked order of relevance.
    Example: ["cyber-security", "ai-engineer"]
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        text = completion.choices[0].message.content.strip()
        
        # Parse result (The model might return a JSON with a key or just an array)
        data = json.loads(text)
        if isinstance(data, dict):
            # Try to find a list in the dict
            for key in ["slugs", "ranked_slugs", "results"]:
                if key in data and isinstance(data[key], list):
                    ranked_slugs = data[key]
                    break
            else:
                # If no key found, assume it's garbage or a flat array in values
                return roles
        else:
            ranked_slugs = data
            
        # Re-order the original role dicts based on the LLM's ranked slugs
        slug_to_role = {r['slug']: r for r in roles}
        final_results = []
        for slug in ranked_slugs:
            if slug in slug_to_role:
                final_results.append(slug_to_role[slug])
        
        return final_results if final_results else roles
    except Exception as e:
        logger.error(f"Error reranking roles: {e}")
        return roles
