# agents/bot_agent.py
from openai import Agent, ModelSettings
from tools.order_tools import get_order_status
from guardrails import sentiment_guard 

BotAgent = Agent(
    name="Customer Support Bot",
    instructions="""
    You are a support assistant. 
    Handle FAQs, track orders, and escalate when unsure or customer upset.
    """,
    model="gemini-1.5-pro",   # Use Gemini API key
    model_settings=ModelSettings(
        tool_choice="auto",   # let the model decide when to use tools
        metadata={"customer_id": "CUST-001"}
    ),
    tools=[get_order_status],
    guardrails=[sentiment_guard],
)
