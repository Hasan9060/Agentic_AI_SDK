import aiohttp
from decouple import config

TAVILY_API_KEY = config("TAVILY_API_KEY")


class Tool:
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func

    async def run(self, *args, **kwargs):
        return await self.func(*args, **kwargs)


async def web_search_tool(query: str) -> str:
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    payload = {"query": query, "search_depth": "basic", "max_results": 5}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                return f"Error: {response.status}"
            data = await response.json()

    results = data.get("results", [])
    if not results:
        return "No results found."

    return "\n\n".join(
        [f"🔹 {r.get('title','No title')}\n{r.get('url','No URL')}\n{r.get('content','')[:200]}..." for r in results]
    )


WebSearchTool = Tool(
    name="web_search",
    description="Search the web using Tavily API",
    func=web_search_tool
)
