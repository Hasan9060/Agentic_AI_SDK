from agents import Agent, function_tool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class WeatherRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=50, description="City for weather information")

@function_tool
def find_weather(city: str) -> str:
    """Get weather information for a city with input validation"""
    try:
        # Validate input using Pydantic model
        request = WeatherRequest(city=city)
        
        # Simulate weather API call
        weather_data = {
            "Islamabad": "25°C, Sunny",
            "Lahore": "35°C, Partly Cloudy",
            "Karachi": "32°C, Humid",
            "Peshawar": "30°C, Clear",
        }
        
        weather = weather_data.get(
            request.city, 
            f"Weather information not available for {request.city}"
        )
        
        return f"Weather in {request.city}: {weather}"
        
    except Exception as e:
        logger.error(f"Weather search error: {str(e)}")
        return f"I apologize, but I encountered an error getting weather information: {str(e)}"

weather_agent = Agent(
    name="WeatherAgent",
    instructions="""
    You are a weather agent specialized in providing weather information.
    
    Guidelines:
    1. Only provide weather information, not other travel services
    2. Validate all input parameters before searching
    3. If input validation fails, politely ask for corrected information
    4. Be clear that weather information is approximate and may change
    
    Use the find_weather tool for all weather queries.
    For queries outside your scope, hand off to the triage agent.
    """,
    handoff_description="Specialist agent for weather information and forecasts",
    tools=[find_weather],
)