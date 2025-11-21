import asyncio
from tools.search_tools import search_content_examples

async def test():
    # Search WITHOUT platform filter
    result = await search_content_examples(
        query="writing tips advice",
        platform=None,  # No filter
        match_count=10
    )
    print(result)

asyncio.run(test())
