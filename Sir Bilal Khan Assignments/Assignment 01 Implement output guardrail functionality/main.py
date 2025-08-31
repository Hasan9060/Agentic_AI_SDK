from agents import Runner
from my_agent.handoff_agent import triagent
from decouple import config

res = Runner.run_sync(
    starting_agent=triagent,
    input="Who is muslims",
)

print(res.final_output)
