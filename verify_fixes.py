
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from logic.data_sources import fetch_hackernews
from logic.ai_pipeline import extract_json

def test_hackernews():
    print("\n--- Testing HackerNews Algolia Integration ---")
    signals = fetch_hackernews()
    if signals:
        print(f"[OK] Success: Found {len(signals)} hiring signals.")
        for i, s in enumerate(signals):
            print(f"  [{i+1}] {s[:100]}...")
    else:
        print("❌ Failed: No hiring signals found via Algolia.")

def test_json_fallback():
    print("\n--- Testing AI JSON Parsing Fallback ---")
    
    # Case 1: Malformed JSON
    bad_text = "This is not json at all { {{ ["
    result = extract_json(bad_text)
    if result and result.get("error"):
        print("[OK] Case 1 (Total Garbage) passed: Returned error object.")
    else:
        print("[FAIL] Case 1 (Total Garbage) failed: Did not return expected error object.")

    # Case 2: Markdown JSON
    md_text = "```json\n{\"test\": true}\n```"
    result = extract_json(md_text)
    if result and result.get("test"):
        print("[OK] Case 2 (Markdown) passed: Stripped and parsed correctly.")
    else:
        print("[FAIL] Case 2 (Markdown) failed.")

    # Case 3: Embedded JSON
    embedded_text = "Analysis complete here is the data: {\"status\": \"ok\"} hope this helps."
    result = extract_json(embedded_text)
    if result and result.get("status") == "ok":
        print("[OK] Case 3 (Embedded) passed: Regex extracted correctly.")
    else:
        print("[FAIL] Case 3 (Embedded) failed.")

if __name__ == "__main__":
    test_hackernews()
    test_json_fallback()
