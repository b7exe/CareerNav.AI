import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL = "meta/llama-3.1-405b-instruct"

print(f"Testing NVIDIA API with key: {API_KEY[:10]}...")

try:
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=API_KEY
    )
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Hello, respond with one word."}],
        max_tokens=10
    )
    print(f"SUCCESS! Response: {completion.choices[0].message.content}")
except Exception as e:
    print(f"FAILED! Error: {e}")
