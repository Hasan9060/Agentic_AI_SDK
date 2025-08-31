# guardrails/sentiment_guard.py
from openai import guardrail

NEGATIVE_WORDS = ["stupid", "idiot", "hate", "worst"]

@guardrail
def sentiment_guard(query: str) -> str | None:
    """Detects offensive/negative language and rephrases or blocks"""
    if any(word in query.lower() for word in NEGATIVE_WORDS):
        return "⚠️ Please keep the conversation respectful. Try rephrasing your query."
    return None  # allow normal flow
