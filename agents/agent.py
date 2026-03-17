import aiohttp
import asyncio

from api_provider import APIProvider # Import the APIProvider class from the api_provider module
MASTER_URL = "http://master:5000/agent"


api_key = APIProvider().openrouter()
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