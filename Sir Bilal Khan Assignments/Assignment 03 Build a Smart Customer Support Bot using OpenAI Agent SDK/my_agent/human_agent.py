# agents/human_agent.py
from openai import Agent

HumanAgent = Agent(
    name="Human Support Agent",
    instructions="You are a human agent. Take over when escalation is required.",
    model="gemini-1.5-pro"
)
