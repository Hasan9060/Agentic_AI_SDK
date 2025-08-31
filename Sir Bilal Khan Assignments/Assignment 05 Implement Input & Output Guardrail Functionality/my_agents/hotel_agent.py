from agents import Agent, function_tool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class HotelSearchRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=50, description="City for hotel search")
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$', description="Date in YYYY-MM-DD format")

@function_tool
def find_hotels(city: str, date: str) -> str:
    """Find available hotels in a city with input validation"""
    try:
        # Validate input using Pydantic model
        request = HotelSearchRequest(city=city, date=date)
        
        # Simulate hotel search
        return f"""Hotels available in {request.city} on {request.date}:
        
        - PC Hotel: 15,000 PKR per night, Breakfast included, Free parking
        - Marriott: 13,000 PKR per night, Breakfast included, Free parking
        - Movenpick: 14,000 PKR per night, Breakfast included, Free WiFi
        
        Rates are subject to availability and taxes. Contact our booking service for reservations.
        """
        
    except Exception as e:
        logger.error(f"Hotel search error: {str(e)}")
        return f"I apologize, but I encountered an error searching for hotels: {str(e)}"

hotel_agent = Agent(
    name="HotelAgent",
    instructions="""
    You are a hotel agent specialized in finding accommodation information.
    
    Guidelines:
    1. Only provide hotel information, not other travel services
    2. Never ask for or store sensitive payment information
    3. Clearly state that users need to contact booking services for reservations
    4. Validate all input parameters before searching
    5. If input validation fails, politely ask for corrected information
    
    Use the find_hotels tool for all hotel searches.
    For queries outside your scope, hand off to the triage agent.
    """,
    handoff_description="Specialist agent for hotel information and availability",
    tools=[find_hotels],
)