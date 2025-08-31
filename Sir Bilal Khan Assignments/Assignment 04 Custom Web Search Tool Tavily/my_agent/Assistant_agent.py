from websearchtool.tavilytool import WebSearchTool

class GeminiAgent:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    async def run(self, prompt: str):
        tool = self.tools.get("web_search")
        if tool:
            return await tool.run(prompt)
        return f"Agent Response: I got your prompt: '{prompt}'"


agent = GeminiAgent(tools=[WebSearchTool])
