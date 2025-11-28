import requests
import json

OLLAMA_URL = "http://localhost:11434/api/tags"

print(f"Testing Ollama connection at: {OLLAMA_URL}")

try:
    response = requests.get(OLLAMA_URL, timeout=5)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ Ollama is RUNNING!")
        models = response.json().get("models", [])
        print(f"Available models: {[m['name'] for m in models]}")

        # Check if llama3.1:8b is available
        if any("llama3.1:8b" in m["name"] for m in models):
            print("✅ 'llama3.1:8b' is available.")
        else:
            print(
                "⚠️ 'llama3.1:8b' NOT found in model list. You may need to run 'ollama pull llama3.1:8b'"
            )
    else:
        print("❌ Ollama returned error status.")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Connection REFUSED. Is Ollama running?")
    print("Try running 'ollama serve' in a separate terminal.")
except Exception as e:
    print(f"❌ Error: {e}")
