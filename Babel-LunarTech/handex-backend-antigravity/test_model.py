import openai
import os

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    exit(1)

client = openai.OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "Hello"}],
        max_completion_tokens=10
    )
    print("Success! Model exists.")
except Exception as e:
    print(f"Error: {e}")
