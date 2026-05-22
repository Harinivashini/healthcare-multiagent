"""
agents/llm_client.py
─────────────────────
Groq API wrapper — compatible with groq==0.11.0
"""

import os


def chat(
    system_prompt: str,
    user_message: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set. Check your .env file.")

    # Use model from env, default to openai/gpt-oss-120b
    model = model or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

    client = Groq(api_key=api_key)

    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    )
    return completion.choices[0].message.content.strip()