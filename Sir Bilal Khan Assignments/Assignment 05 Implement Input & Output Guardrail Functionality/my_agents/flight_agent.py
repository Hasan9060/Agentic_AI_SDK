from agents import Agent, function_tool
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class FlightSearchRequest(BaseModel):
    from_city: str = Field(..., min_length=1, max_length=50, description="Departure city")
    to_city: str = Field(..., min_length=1, max_length=50, description="Destination city")
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$', description="Date in YYYY-MM-DD format")

@function_tool
def find_flights(from_city: str, to_city: str, date: str) -> str:
    """Find available flights between cities with input validation"""
    try:
        # Validate input using Pydantic model
        request = FlightSearchRequest(
            from_city=from_city,
            to_city=to_city,
            date=date
        )
        
        # Simulate flight search
        return f"""Available flights from {request.from_city} to {request.to_city} on {request.date}:
        
        - Flight PK100: Departure 08:00, Arrival 10:30, Price: 28,000 PKR
        - Flight EK202: Departure 14:00, Arrival 16:45, Price: 35,000 PKR
        - Flight TK708: Departure 19:30, Arrival 22:15, Price: 31,500 PKR
        
        Prices include taxes. Please contact our booking service for reservations.
        """
        
    except Exception as e:
        logger.error(f"Flight search error: {str(e)}")
        return f"I apologize, but I encountered an error searching for flights: {str(e)}"

flight_agent = Agent(
    name="FlightAgent",
    instructions="""
    You are a flight agent specialized in finding flight information.
    
    Guidelines:
    1. Only provide flight information, not other travel services
    2. Never ask for or store sensitive payment information
    3. Clearly state that users need to contact booking services for reservations
    4. Validate all input parameters before searching
    5. If input validation fails, politely ask for corrected information
    
    Use the find_flights tool for all flight searches.
    For queries outside your scope, hand off to the triage agent.
    """,
    handoff_description="Specialist agent for flight information and availability",
    tools=[find_flights],
)