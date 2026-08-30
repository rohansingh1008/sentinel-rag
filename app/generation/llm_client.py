import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

def generate_answer(prompt: str, max_tokens: int = 800) -> str:
    """Sends a prompt to the LLM and returns the generated answer."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        finish_reason = response.choices[0].finish_reason
        print(f"[WARNING] Empty response from LLM. finish_reason={finish_reason}")
    return content or ""