import os
import logging
from typing import Dict, Any, Literal, Optional
from dotenv import load_dotenv
from openai import OpenAI
from openai.agents.agent import Agent, Runner
from openai.agents.conversation import Turn
from openai.agents.tools import function_tool, guardrail
from openai.types import ModelSettings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("support_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simulated order database
ORDERS = {
    "ORD12345": {"status": "Shipped", "items": ["Wireless Headphones", "Charging Cable"], "customer": "John Doe"},
    "ORD67890": {"status": "Processing", "items": ["Smart Watch"], "customer": "Jane Smith"},
    "ORD11121": {"status": "Delivered", "items": ["Laptop Bag", "USB-C Adapter"], "customer": "Robert Johnson"}
}

# Product FAQs knowledge base
PRODUCT_FAQS = {
    "return policy": "We offer a 30-day return policy on all unused items with original packaging.",
    "shipping time": "Standard shipping takes 3-5 business days. Express shipping is available for an additional fee.",
    "warranty": "All products come with a 1-year manufacturer warranty. Extended warranties are available.",
    "payment methods": "We accept all major credit cards, PayPal, and Apple Pay.",
    "contact support": "You can reach our support team at support@example.com or 1-800-123-4567 from 9AM to 5PM EST."
}

class SentimentAnalyzer:
    """Simple sentiment analysis for guardrails"""
    
    @staticmethod
    def analyze(text: str) -> Literal["positive", "neutral", "negative"]:
        text_lower = text.lower()
        
        negative_words = ["hate", "terrible", "awful", "horrible", "stupid", "suck", "angry", "pissed", "frustrated"]
        positive_words = ["love", "great", "awesome", "fantastic", "wonderful", "thank", "appreciate", "helpful"]
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"

# Guardrail to check for offensive language
@guardrail
def check_offensive_language(turn: Turn) -> Optional[str]:
    """Guardrail to detect and handle offensive language"""
    offensive_terms = ["stupid", "idiot", "moron", "shit", "fuck", "asshole", "suck"]
    user_message = turn.user_message.content.lower()
    
    for term in offensive_terms:
        if term in user_message:
            logger.warning(f"Offensive language detected: {term}")
            return "I understand you're frustrated, but please maintain a respectful tone. How can I help resolve your issue?"
    
    return None

# Function tool with advanced features
@function_tool(
    is_enabled=lambda turn: any(keyword in turn.user_message.content.lower() 
                               for keyword in ["order", "status", "tracking", "delivery"]),
    error_function=lambda turn, error: f"I couldn't find that order. Please check your order ID and try again."
)
def get_order_status(order_id: str) -> str:
    """Get the status of an order by its ID"""
    logger.info(f"Fetching status for order: {order_id}")
    
    if order_id.upper() in ORDERS:
        order = ORDERS[order_id.upper()]
        items = ", ".join(order["items"])
        return f"Order {order_id.upper()} for {order['customer']} is currently {order['status']}. Items: {items}."
    else:
        raise ValueError(f"Order {order_id} not found in our system")

@function_tool
def search_faqs(query: str) -> str:
    """Search for answers to frequently asked questions"""
    logger.info(f"Searching FAQs for: {query}")
    query_lower = query.lower()
    
    for keyword, answer in PRODUCT_FAQS.items():
        if keyword in query_lower:
            return answer
    
    return "I couldn't find a specific answer to your question. Would you like to speak with a human agent for more assistance?"

class BotAgent(Agent):
    def __init__(self):
        super().__init__(
            model="gpt-4-turbo",
            model_settings=ModelSettings(
                tool_choice="auto",
                temperature=0.3,
                metadata={
                    "customer_id": "default",
                    "bot_version": "2.1",
                    "department": "customer_support"
                }
            ),
            tools=[get_order_status, search_faqs],
            instructions="""You are a friendly customer support bot for TechGadgets Inc.
            
            Your capabilities:
            1. Answer product and service FAQs using the search_faqs tool
            2. Check order status using the get_order_status tool
            3. Escalate to human support when needed
            
            Guidelines:
            - Be polite, empathetic, and professional
            - If a user seems frustrated or angry, offer to escalate to human support
            - Always verify order IDs before looking them up
            - If you can't help with a query, escalate to human support
            - Keep responses concise but helpful"""
        )
    
    def should_handoff(self, turn: Turn) -> bool:
        """Determine if a conversation should be handed off to a human"""
        sentiment = SentimentAnalyzer.analyze(turn.user_message.content)
        
        # Handoff conditions
        handoff_keywords = ["human", "agent", "representative", "manager", "supervisor"]
        contains_handoff_keyword = any(keyword in turn.user_message.content.lower() 
                                      for keyword in handoff_keywords)
        
        complex_queries = ["complaint", "refund", "return", "compensation", "lawsuit"]
        is_complex_query = any(keyword in turn.user_message.content.lower() 
                              for keyword in complex_queries)
        
        return (sentiment == "negative" or contains_handoff_keyword or is_complex_query)

class HumanAgent(Agent):
    def __init__(self):
        super().__init__(
            model="gpt-4-turbo",
            model_settings=ModelSettings(
                temperature=0.7,
                metadata={
                    "role": "human_support_agent",
                    "department": "customer_support"
                }
            ),
            instructions="""You are a human customer support agent. 
            
            Guidelines:
            - Show empathy and understanding for customer issues
            - Provide detailed, personalized assistance
            - For order issues, ask for order ID and check the system
            - For complex issues, note them for follow-up
            - Always provide your name (use 'Alex') and offer further assistance
            - If you can't resolve an issue immediately, promise a callback or email follow-up"""
        )

def main():
    """Run the customer support bot"""
    logger.info("Starting customer support bot")
    
    # Initialize agents
    bot_agent = BotAgent()
    human_agent = HumanAgent()
    
    print("=" * 50)
    print("TechGadgets Inc. Customer Support")
    print("Type 'exit' at any time to end the conversation")
    print("=" * 50)
    
    # Conversation history
    conversation_history = []
    
    while True:
        try:
            user_input = input("\nCustomer: ").strip()
            
            if user_input.lower() == 'exit':
                print("Thank you for contacting TechGadgets support. Have a great day!")
                break
            
            # Create conversation turn
            turn = Turn(user_message={"role": "user", "content": user_input})
            
            # Add to conversation history
            conversation_history.append(f"Customer: {user_input}")
            
            # Check for offensive language first
            offensive_check = check_offensive_language(turn)
            if offensive_check:
                print(f"Support: {offensive_check}")
                conversation_history.append(f"Support: {offensive_check}")
                continue
            
            # Determine which agent to use
            if bot_agent.should_handoff(turn):
                logger.info("Handing off to human agent")
                print("Support: I'm connecting you with a human support agent...")
                response = Runner.run(human_agent, turn)
            else:
                response = Runner.run(bot_agent, turn)
            
            # Get the response
            support_response = response.messages[-1].content
            print(f"Support: {support_response}")
            conversation_history.append(f"Support: {support_response}")
            
        except Exception as e:
            logger.error(f"Error in conversation: {str(e)}")
            print("Support: I'm experiencing technical difficulties. Please try again in a moment.")
    
    # Log the entire conversation
    logger.info("Conversation ended. Full transcript:\n" + "\n".join(conversation_history))

if __name__ == "__main__":
    main()