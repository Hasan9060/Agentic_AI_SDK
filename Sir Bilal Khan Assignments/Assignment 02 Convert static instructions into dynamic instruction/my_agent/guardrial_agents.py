# guardrial_agents.py
from agents import Agent
from my_config.gemini_confg import MODEL
from data_schema.myDataSchema import MyDataType

guardrial_agent = Agent(
    name="Guardrail Agent for Hotels",
    instructions="""
    Check if queries are about any hotel in our database.
    Return is_query_about_hotel_sannata as True if the query is about any hotel,
    not just Hotel Sannata.
    """,
    model=MODEL,
    output_type=MyDataType
)