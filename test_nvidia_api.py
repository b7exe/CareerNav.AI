import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://integrate.api.nvidia.com/v1/chat/completions"
api_key = os.getenv("NVIDIA_API_KEY")

headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}

payload = {
  "model": "meta/llama-3.3-70b-instruct",
  "messages": [{"role": "user", "content": "say hello"}],
  "temperature": 0.5,
  "top_p": 1,
  "max_tokens": 1024
}

print(f"Testing NVIDIA API at: {url}")
print(f"Model: {payload['model']}")

try:
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response:")
        print(response.json()['choices'][0]['message']['content'])
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
