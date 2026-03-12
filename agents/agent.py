import aiohttp
import asyncio

MASTER_URL = "http://master:5000/agent"

async def main():

    data = {
        "agent_id": "agent1",
        "text": "Hello master"
    }

    async with aiohttp.ClientSession() as session:
        response = await session.post(MASTER_URL, json=data)

        result = await response.json()

        print("Response:", result)

        await session.close()

asyncio.run(main())