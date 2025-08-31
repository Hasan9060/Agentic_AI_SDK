from typing import Literal, List, Dict, Any, Optional
from agents import (
    Agent,
    HandoffInputData,
    RunContextWrapper,
    Runner,
    RunConfig,
    TResponseInputItem,
    handoff,
)
from pydantic import BaseModel, Field, validator
import re
import logging

from my_agents.weather_agent import weather_agent
from my_agents.hotel_agent import hotel_agent
from my_agents.flight_agent import flight_agent
from my_config import model
from agents.extensions import handoff_filters

import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Users(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    role: Literal["admin", "super user", "basic"]
    age: int = Field(..., ge=0, le=120)
    
    @validator('name')
    def name_must_be_valid(cls, v):
        if not re.match(r'^[a-zA-Z\s]+$', v):
            raise ValueError('Name must contain only letters and spaces')
        return v.title()

class ComplianceRules(BaseModel):
    """Global compliance rules for all agents"""
    blocked_terms: List[str] = Field(
        default_factory=lambda: ["credit card", "password", "ssn", "social security"]
    )
    allowed_domains: List[str] = Field(
        default_factory=lambda: ["weather.com", "booking.com", "expedia.com"]
    )
    max_response_length: int = 1000
    require_content_moderation: bool = True

class GuardrailResult(BaseModel):
    passed: bool
    message: str = ""
    modified_input: Optional[List[TResponseInputItem]] = None
    modified_output: Optional[str] = None

class GuardrailManager:
    """Manages input and output guardrails for agents"""
    
    def __init__(self, compliance_rules: ComplianceRules):
        self.compliance_rules = compliance_rules
    
    async def validate_input(
        self, 
        input_data: List[TResponseInputItem], 
        agent_name: str,
        user_context: Users
    ) -> GuardrailResult:
        """Validate input against various guardrails"""
        try:
            # Check for empty input
            if not input_data or not any(item.get('content') for item in input_data):
                return GuardrailResult(
                    passed=False,
                    message="Input cannot be empty"
                )
            
            # Process each input item
            modified_items = []
            for item in input_data:
                if item.get('role') == 'user' and 'content' in item:
                    content = item['content']
                    
                    # Check for blocked terms
                    for term in self.compliance_rules.blocked_terms:
                        if term.lower() in content.lower():
                            logger.warning(f"Blocked term detected: {term}")
                            return GuardrailResult(
                                passed=False,
                                message=f"Input contains prohibited term: {term}"
                            )
                    
                    # Sanitize input (remove special characters that might indicate injection)
                    sanitized_content = re.sub(r'[<>{}|\\^~\[\]`]', '', content)
                    if sanitized_content != content:
                        logger.info(f"Sanitized input from {content} to {sanitized_content}")
                    
                    modified_items.append({
                        'role': item['role'],
                        'content': sanitized_content[:500]  # Limit input length
                    })
                else:
                    modified_items.append(item)
            
            return GuardrailResult(
                passed=True,
                message="Input validation passed",
                modified_input=modified_items
            )
            
        except Exception as e:
            logger.error(f"Input validation error: {str(e)}")
            return GuardrailResult(
                passed=False,
                message=f"Input validation error: {str(e)}"
            )
    
    async def validate_output(
        self, 
        output: str, 
        agent_name: str,
        user_context: Users
    ) -> GuardrailResult:
        """Validate output against various guardrails"""
        try:
            # Check for empty output
            if not output or not output.strip():
                return GuardrailResult(
                    passed=False,
                    message="Output cannot be empty"
                )
            
            # Check length限制
            if len(output) > self.compliance_rules.max_response_length:
                truncated_output = output[:self.compliance_rules.max_response_length] + "..."
                logger.warning(f"Output truncated for length compliance")
                return GuardrailResult(
                    passed=True,
                    message="Output truncated due to length限制",
                    modified_output=truncated_output
                )
            
            # Check for blocked terms in output
            for term in self.compliance_rules.blocked_terms:
                if term.lower() in output.lower():
                    logger.warning(f"Blocked term detected in output: {term}")
                    return GuardrailResult(
                        passed=False,
                        message=f"Output contains prohibited term: {term}"
                    )
            
            # Check for PII (simplified example)
            pii_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{16}\b',  # Credit card
            ]
            
            modified_output = output
            for pattern in pii_patterns:
                matches = re.findall(pattern, output)
                if matches:
                    logger.warning(f"PII detected in output: {matches}")
                    for match in matches:
                        modified_output = modified_output.replace(match, "[REDACTED]")
            
            if modified_output != output:
                return GuardrailResult(
                    passed=True,
                    message="PII redacted from output",
                    modified_output=modified_output
                )
            
            return GuardrailResult(
                passed=True,
                message="Output validation passed",
                modified_output=output
            )
            
        except Exception as e:
            logger.error(f"Output validation error: {str(e)}")
            return GuardrailResult(
                passed=False,
                message=f"Output validation error: {str(e)}"
            )

# Global compliance rules
compliance_rules = ComplianceRules()
guardrail_manager = GuardrailManager(compliance_rules)

async def handoff_permission(ctx: RunContextWrapper[Users], agent: Agent) -> bool:
    """Enhanced handoff permission with role-based access control"""
    if ctx.context.age < 18:
        logger.warning(f"User {ctx.context.name} is underage for handoff")
        return False

    if ctx.context.role == "super user":
        return True
        
    if ctx.context.role == "admin" and agent.name in ["FlightAgent", "HotelAgent"]:
        return True
        
    if ctx.context.role == "basic" and agent.name == "WeatherAgent":
        return True
        
    logger.warning(f"Handoff not permitted for {ctx.context.role} to {agent.name}")
    return False

def handoff_filter(data: HandoffInputData) -> HandoffInputData:
    """Enhanced handoff filter with guardrails"""
    # Remove all tools first
    data = handoff_filters.remove_all_tools(data)
    
    # Get recent history (last 2 exchanges)
    history = data.input_history[-2:]
    
    # Apply additional filtering
    filtered_history = []
    for item in history:
        if item.get('role') in ['user', 'assistant'] and 'content' in item:
            # Simple content filter
            content = item['content']
            for term in compliance_rules.blocked_terms:
                if term in content.lower():
                    content = content.replace(term, '[FILTERED]')
            filtered_history.append({**item, 'content': content})
        else:
            filtered_history.append(item)
    
    return HandoffInputData(
        input_history=filtered_history,
        new_items=data.new_items,
        pre_handoff_items=data.pre_handoff_items,
    )

# Enhanced triage agent with guardrails
triage_agent = Agent(
    name="TriageAgent",
    instructions="""
    You are a triage agent. Your responsibilities:
    1. Analyze user queries and hand off to appropriate specialist agents
    2. Enforce content guidelines and compliance rules
    3. Filter inappropriate content before handoff
    4. Provide helpful responses for general queries
    
    Specialist agents available:
    - FlightAgent: For flight-related queries (booking, availability, prices)
    - HotelAgent: For hotel-related queries (booking, availability, prices)
    - WeatherAgent: For weather-related queries (forecasts, conditions)
    
    For any queries involving sensitive information, politely decline and explain limitations.
    """,
    handoffs=[
        handoff(
            agent=weather_agent,
            tool_name_override="handoff_weatheragent",
            tool_description_override="Handoff to weather agent for weather information",
            is_enabled=handoff_permission,
            input_filter=handoff_filter,
        ),
        handoff(
            agent=hotel_agent,
            tool_name_override="handoff_hotelagent",
            tool_description_override="Handoff to hotel agent for accommodation information",
            is_enabled=handoff_permission,
            input_filter=handoff_filter,
        ),
        handoff(
            agent=flight_agent,
            tool_name_override="handoff_flightagent",
            tool_description_override="Handoff to flight agent for travel information",
            is_enabled=handoff_permission,
            input_filter=handoff_filter,
        ),
    ],
    handoff_description="""
    This triage agent coordinates between specialized agents for travel planning.
    Hand off to flight, hotel, or weather agents based on query content.
    For general queries, respond directly without handoff.
    """,
)

# Add circular handoffs for return routing
weather_agent.handoffs.append(triage_agent)
hotel_agent.handoffs.append(triage_agent)
flight_agent.handoffs.append(triage_agent)

async def run_with_guardrails(
    agent: Agent,
    input_data: List[TResponseInputItem],
    run_config: RunConfig,
    context: Users
) -> Any:
    """Run agent with comprehensive guardrails"""
    try:
        # Input validation
        input_validation = await guardrail_manager.validate_input(
            input_data, agent.name, context
        )
        
        if not input_validation.passed:
            return {
                "error": True,
                "message": f"Input validation failed: {input_validation.message}",
                "output": "I apologize, but I cannot process this request due to content restrictions."
            }
        
        # Use modified input if available
        validated_input = input_validation.modified_input or input_data
        
        # Execute the agent
        result = await Runner.run(
            agent,
            input=validated_input,
            run_config=run_config,
            context=context,
        )
        
        # Output validation
        output_validation = await guardrail_manager.validate_output(
            result.final_output, agent.name, context
        )
        
        if not output_validation.passed:
            return {
                "error": True,
                "message": f"Output validation failed: {output_validation.message}",
                "output": "I apologize, but I cannot provide this response due to content restrictions."
            }
        
        # Use modified output if available
        result.final_output = output_validation.modified_output or result.final_output
        
        return result
        
    except Exception as e:
        logger.error(f"Error in run_with_guardrails: {str(e)}")
        return {
            "error": True,
            "message": f"System error: {str(e)}",
            "output": "I apologize, but I'm experiencing technical difficulties. Please try again later."
        }

async def main():
    """Main function with enhanced guardrails"""
    user = Users(name="John Doe", role="super user", age=30)
    start_agent = triage_agent
    input_data: list[TResponseInputItem] = []
    
    print("Travel Assistant with Guardrails")
    print("Type 'exit' to quit, 'help' for assistance")
    
    while True:
        try:
            user_prompt = input("\nEnter your query: ").strip()
            
            if user_prompt.lower() == 'exit':
                break
                
            if user_prompt.lower() == 'help':
                print("""
                Available services:
                - Flight information and bookings
                - Hotel reservations and information
                - Weather forecasts and conditions
                - General travel advice
                
                Please avoid sharing sensitive personal information.
                """)
                continue
                
            if not user_prompt:
                print("Please enter a valid query")
                continue
                
            # Add user input to history
            input_data.append({"role": "user", "content": user_prompt})
            
            # Run with guardrails
            result = await run_with_guardrails(
                start_agent,
                input_data=input_data,
                run_config=RunConfig(model=model, tracing_disabled=False),
                context=user,
            )
            
            if hasattr(result, 'last_agent'):
                start_agent = result.last_agent
                input_data = result.to_input_list()
                
                # Display result
                print(f"\nAssistant: {result.final_output}")
                
                # Log the interaction
                logger.info(f"User: {user_prompt} | Agent: {start_agent.name} | Output: {result.final_output[:100]}...")
            else:
                # Handle error case
                print(f"\nError: {result.get('output', 'Unknown error')}")
                # Reset to triage agent on error
                start_agent = triage_agent
                # Keep recent history but remove the problematic input
                if input_data and input_data[-1].get('content') == user_prompt:
                    input_data.pop()
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            logger.error(f"Unexpected error in main loop: {str(e)}")
            # Reset to a known good state
            start_agent = triage_agent
            input_data = []

if __name__ == "__main__":
    asyncio.run(main())