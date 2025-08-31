import asyncio
from my_agent.Assistant_agent import agent

async def main():
    query = "current president of the Srilanka?"
    result = await agent.run(query)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
