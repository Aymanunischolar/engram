import os

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("LLM_API_KEY"):
    raise RuntimeError(
        "LLM_API_KEY is not set. Copy .env.example to .env and add your OpenAI API key."
    )
