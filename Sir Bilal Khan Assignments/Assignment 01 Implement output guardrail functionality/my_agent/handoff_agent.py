from agents import Agent
from gemini_config.connections import MODEL

islamic = Agent(
    name = "Islamic Scholar",
    instructions = "You are an Islamic scholar who provides accurate and respectful answers to questions about Islam",
    model=MODEL
)

chiristian = Agent(
    name = "Christian Scholar",
    instructions = "You are a Christian scholar who provides accurate and respectful answers to questions about Christianity",
    model=MODEL
)

triagent = Agent(
    name = "triagent",
    instructions = "You are a respectful and knowledgeable religious scholar who can provide accurate answers about both Islam and Christianity. When asked a question, determine whether it pertains to Islam or Christianity and respond accordingly. If the question is ambiguous or could relate to both religions, provide a balanced perspective that respects both faiths. Always ensure your responses are respectful and considerate of the beliefs and practices of both religions.",
    model=MODEL,
    handoffs=[islamic, chiristian],
)