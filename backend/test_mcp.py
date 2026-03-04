import asyncio
from agent.mcp_client import mcp_client

async def test():
    tools = await mcp_client.get_tools()
    print("Tools type:", type(tools))
    for t in tools:
        print(t.name)

asyncio.run(test())
