import os
from dotenv import load_dotenv
from openai.agents.agent import Agent, Runner
from openai.agents.conversation import Turn
from openai.agents.tools import function_tool
from openai.types import ModelSettings

load_dotenv()

# Demo 1: Tool choice settings
def demo_tool_choice():
    """Showcase different tool_choice settings"""
    
    @function_tool
    def get_weather(location: str) -> str:
        return f"Weather in {location}: Sunny, 72°F"
    
    # Auto - let the model decide
    agent_auto = Agent(
        model="gpt-4-turbo",
        model_settings=ModelSettings(tool_choice="auto"),
        tools=[get_weather],
        instructions="Answer user questions, using tools when appropriate."
    )
    
    # Required - force tool use
    agent_required = Agent(
        model="gpt-4-turbo",
        model_settings=ModelSettings(tool_choice="required"),
        tools=[get_weather],
        instructions="Answer user questions, using tools when appropriate."
    )
    
    # None - no tool use
    agent_none = Agent(
        model="gpt-4-turbo",
        model_settings=ModelSettings(tool_choice="none"),
        tools=[get_weather],
        instructions="Answer user questions, using tools when appropriate."
    )
    
    test_turn = Turn(user_message={"role": "user", "content": "What's the weather in New York?"})
    
    print("=== Tool Choice Demo ===")
    print("Auto setting:", Runner.run(agent_auto, test_turn).messages[-1].content)
    print("Required setting:", Runner.run(agent_required, test_turn).messages[-1].content)
    print("None setting:", Runner.run(agent_none, test_turn).messages[-1].content)

# Demo 2: Metadata usage
def demo_metadata():
    """Showcase metadata usage"""
    
    agent_with_metadata = Agent(
        model="gpt-4-turbo",
        model_settings=ModelSettings(
            metadata={
                "customer_tier": "premium",
                "conversation_type": "support",
                "agent_id": "bot-123"
            }
        ),
        instructions="You are a support agent. Check metadata for customer context."
    )
    
    test_turn = Turn(user_message={"role": "user", "content": "What do you know about me?"})
    
    print("\n=== Metadata Demo ===")
    response = Runner.run(agent_with_metadata, test_turn)
    print("Response:", response.messages[-1].content)

# Demo 3: Conditional tool enabling
def demo_conditional_tools():
    """Showcase conditional tool enabling"""
    
    @function_tool(
        is_enabled=lambda turn: "stock" in turn.user_message.content.lower()
    )
    def check_stock(item: str) -> str:
        return f"Item {item} is in stock."
    
    agent = Agent(
        model="gpt-4-turbo",
        tools=[check_stock],
        instructions="Help users with their queries."
    )
    
    print("\n=== Conditional Tools Demo ===")
    
    # This should use the tool
    stock_turn = Turn(user_message={"role": "user", "content": "Do you have iPhone in stock?"})
    stock_response = Runner.run(agent, stock_turn)
    print("With 'stock' keyword:", stock_response.messages[-1].content)
    
    # This should not use the tool
    other_turn = Turn(user_message={"role": "user", "content": "What's your return policy?"})
    other_response = Runner.run(agent, other_turn)
    print("Without 'stock' keyword:", other_response.messages[-1].content)

if __name__ == "__main__":
    demo_tool_choice()
    demo_metadata()
    demo_conditional_tools()