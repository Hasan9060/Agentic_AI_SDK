from agents import Agent
from gemini_config.connections import MODEL

agent = Agent(
    name = "Assistant",
    instructions = "You are a helpful assistant that can search the web for information.",
    model=MODEL
)