import time
from openai import OpenAI

# Connect directly to the local background server
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

print("[PING] Requesting ACK from Llama 3.1...")
start = time.time()

try:
    response = client.chat.completions.create(
        model="llama3.1",
        messages=[{"role": "user", "content": "Respond with exactly one word: ACK."}],
        max_tokens=10,
    )
    elapsed = time.time() - start
    print(f"[SUCCESS] Received: {response.choices[0].message.content}")
    print(f"[TELEMETRY] Connection cleared in {elapsed:.2f} seconds.")
except Exception as e:
    print(f"[ERROR] API is deadlocked or unreachable: {e}")
