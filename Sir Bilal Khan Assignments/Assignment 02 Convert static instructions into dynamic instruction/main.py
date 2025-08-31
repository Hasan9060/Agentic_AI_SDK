# main.py
from agents import Runner, set_tracing_disabled, InputGuardrailTripwireTriggered
from my_agent.hotel_assistant import hotel_assistant
from context import hotel_context
set_tracing_disabled(True)

# Sample context with multiple hotels

prompt = input("Enter your query: ")

try:
    res = Runner.run_sync(
        starting_agent=hotel_assistant, 
        input= prompt,
        context=hotel_context  # Pass the dynamic context
    )
    print(res.final_output)
except InputGuardrailTripwireTriggered as e:
    print(e)