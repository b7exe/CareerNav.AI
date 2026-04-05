import os
import sys
import json
import time
import datetime
import argparse
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL = "meta/llama-3.3-70b-instruct"

JSON_FILE = os.path.join(os.path.dirname(__file__), "logic", "market_data_json.json")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "logic")

REQUIRED_FIELDS = {
    'slug', 'demand_score', 'global_demand', 'ai_disruption_risk', 
    'lifetime', 'avg_salary_india', 'why_now', 'situation', 'fastest_path_to_hired'
}

GLOBAL_DEMAND_ENUM = {'very_high', 'high', 'medium', 'low', 'declining'}
DISRUPTION_RISK_ENUM = {'very_low', 'low', 'medium', 'high', 'very_high'}

SYSTEM_PROMPT = """You are a brutally honest IT job market analyst with deep 
knowledge of the 2026 global and Indian tech hiring landscape.
You have no bias toward making roles sound better than they are.
Your job is to evaluate career paths with surgical precision.

Respond ONLY with a valid JSON array. No markdown. No explanation.
No text before or after. Start with [ and end with ]"""

USER_PROMPT_TEMPLATE = """Evaluate these {n} IT career paths for the 2026 job market.
For each path return honest, differentiated metrics.
Do NOT give every role the same scores.
Do NOT be optimistic about roles being disrupted by AI.
Base your evaluation on real 2026 market conditions in India 
and globally.

Be brutally honest about lifetime. Do NOT default to 
'10+ years' for everything. Examples of honest estimates:
- Basic HTML/CSS developer: '2-3 years before AI handles this'
- AI Engineer: '8-12 years minimum, role evolves but stays relevant'
- Prompt Engineer standalone: '3-5 years then merges into other roles'
- Cloud Architect: '12-15 years, infrastructure complexity grows'
- Data Entry/Basic QA: '1-2 years maximum'
The lifetime must reflect 2026 AI disruption reality specifically.

Paths to evaluate:
{roles_list}

Return a JSON array where each object has exactly these fields:
[
  {{
    "slug": String (the role identifier, same as input),
    "demand_score": Number (0-100, genuinely differentiated),
    "global_demand": "very_high | high | medium | low | declining",
    "ai_disruption_risk": "very_low | low | medium | high | very_high",
    "lifetime": String (honest estimate with AI disruption factored in),
    "avg_salary_india": String (tight realistic range in LPA format),
    "why_now": String (one punchy sentence specific to 2026),
    "situation": String (specific market reality, not generic),
    "fastest_path_to_hired": String (direct route for freshers)
  }}
]"""

def setup_client():
    if not API_KEY:
        print("ERROR: NVIDIA_API_KEY missing in .env")
        sys.exit(1)
    return OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

def validate_batch(response_array, batch_slugs):
    if not isinstance(response_array, list):
        return False, "Response is not a JSON array"
    
    responded_slugs = [item.get('slug') for item in response_array if isinstance(item, dict)]
    missing_slugs = set(batch_slugs) - set(responded_slugs)
    if missing_slugs:
        return False, f"Missing evaluations for slugs: {missing_slugs}"

    for item in response_array:
        slug = item.get('slug', 'UNKNOWN')
        missing_fields = REQUIRED_FIELDS - set(item.keys())
        if missing_fields:
            return False, f"Role {slug} missing fields: {missing_fields}"
        
        try:
            ds = float(item['demand_score'])
            if not 0 <= ds <= 100:
                return False, f"Role {slug} demand_score {ds} out of bounds"
        except:
            return False, f"Role {slug} demand_score is not numeric"

        if item['global_demand'] not in GLOBAL_DEMAND_ENUM:
            return False, f"Role {slug} global_demand invalid enum: {item['global_demand']}"
        
        if item['ai_disruption_risk'] not in DISRUPTION_RISK_ENUM:
            return False, f"Role {slug} ai_disruption_risk invalid enum: {item['ai_disruption_risk']}"

    return True, "Valid"

def extract_json_array(text):
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    if text.startswith("[") and text.endswith("]"):
        return text
    
    start_idx = text.find("[")
    end_idx = text.rfind("]")
    if start_idx != -1 and end_idx != -1:
        return text[start_idx:end_idx+1]
        
    return text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Only process first batch and print results, do not write.")
    args = parser.parse_args()

    client = setup_client()

    if not os.path.exists(JSON_FILE):
        print(f"ERROR: Cannot find {JSON_FILE}")
        sys.exit(1)

    with open(JSON_FILE, "r") as f:
        master_data = json.load(f)

    # 1. Backup before overwriting
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"market_data_json_backup_{timestamp}.json")
    with open(backup_path, "w") as f:
        json.dump(master_data, f, indent=2)
    print(f"Backup created: {backup_path}")

    all_roles = list(master_data.values())
    total_roles = len(all_roles)
    BATCH_SIZE = 10
    batches = [all_roles[i:i + BATCH_SIZE] for i in range(0, total_roles, BATCH_SIZE)]
    
    print(f"Starting recalibration of {total_roles} roles in {len(batches)} batches...")
    
    total_updated = 0
    total_skipped = 0
    start_time = time.time()

    for idx, batch in enumerate(batches):
        current_batch_no = idx + 1
        batch_titles = [r['title'] for r in batch]
        batch_slugs = [r['slug'] for r in batch]
        
        print(f"\nBatch {current_batch_no}/{len(batches)} — Processing: {', '.join(batch_titles)}")

        roles_list_str = "\\n".join([f"- {r['title']} (Slug: {r['slug']}, Core Skills: {r.get('core_skills', [])})" for r in batch])
        user_prompt = USER_PROMPT_TEMPLATE.format(n=len(batch), roles_list=roles_list_str)

        retries = 1
        success = False
        parsed_data = None

        while retries >= 0 and not success:
            try:
                if retries == 0:
                    print(f"Retrying batch {current_batch_no}...", flush=True)
                
                completion = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
                    temperature=0.3,
                    timeout=90
                )
                
                raw_text = completion.choices[0].message.content.strip()
                cleaned_text = extract_json_array(raw_text)
                
                try:
                    parsed_data = json.loads(cleaned_text)
                except json.JSONDecodeError:
                    raise Exception("Output is not valid parseable JSON.")
                
                is_valid, err_msg = validate_batch(parsed_data, batch_slugs)
                if not is_valid:
                    raise Exception(f"Validation Error: {err_msg}")
                
                success = True

            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate limit" in err_str:
                    print("Rate limit hit, waiting 10 seconds...", flush=True)
                    time.sleep(10)
                else:
                    print(f"VALIDATION FAILED for batch {current_batch_no}: {e}", flush=True)
                retries -= 1
        
        if not success:
            total_skipped += len(batch)
            print(f"Batch {current_batch_no} completely failed. Skipping.")
            with open("recalibration_errors.log", "a") as err_f:
                err_f.write(f"Failed Batch {current_batch_no} Slugs: {batch_slugs}\\n")
            continue

        if args.dry_run:
            print("\\n=== DRY RUN MODE: BATCH 1 OUTPUT WOULD BE ===")
            print(json.dumps(parsed_data, indent=2))
            print("=============================================")
            print("Dry run flag active. Stopping after Batch 1. No files overwritten.")
            sys.exit(0)

        # Merge updates
        for item in parsed_data:
            s_slug = item['slug']
            if s_slug in master_data:
                for k in REQUIRED_FIELDS:
                    master_data[s_slug][k] = item[k]
        
        total_updated += len(parsed_data)
        print(f"Batch {current_batch_no}/{len(batches)} — Complete. {len(parsed_data)} roles updated successfully.")
        
        if current_batch_no < len(batches):
            time.sleep(3)

    if not args.dry_run:
        with open(JSON_FILE, "w") as f:
            json.dump(master_data, f, indent=2)

    total_time = round(time.time() - start_time, 2)
    print("\\nRecalibration complete.")
    print(f"Total roles updated: {total_updated}")
    print(f"Total roles skipped: {total_skipped}")
    print(f"Total time taken: {total_time}s")
    print("Run 'python app.py' to see updated scores live.")

if __name__ == "__main__":
    main()
