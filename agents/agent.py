import aiohttp
import asyncio
import json
 # Import the APIProvider class from the api_provider module
MASTER_URL = "http://master:5000/provider/openrouter"
db_connection = "http://master:5000/db/check"


async def test_agent_master():
    data = {
        "agent_id": "agent1",
        "text": "Hello master"
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(MASTER_URL, json=data)

        result = await response.json()

        print("Response:", result)

async def test_agent_db():
    async with aiohttp.ClientSession() as session:
        response = await session.get(db_connection)
        result = await response.json()
        print("DB Check Response:", result)

async def agent_call_master_provider_openrouter_r1():
    data = {
      "model": "deepseek/deepseek-r1",
      "messages": [{"role":"user","content":"What is the meaning of life?"}]
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(MASTER_URL, json=data)
        result = await response.json()
        print("Provider result:", result)
        message = result.get("choices", [{}])[0].get("message", {})
        content = message.get("content")
        reasoning = message.get("reasoning_content")
        out = {
            "model": data["model"],
            "status_code": response.status,
            "reasoning": reasoning,
            "answer": content,
            "raw_result": result
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))


@app.route("/radio-metrics", methods=["GET"])
def get_metrics():

    
    data = {
        "throughput": random.randint(200,600),
        "mcs": random.randint(5,28),
        "prb": random.randint(10,100)
    }

    return jsonify(data)


async def main():
    # await agent_call_master_provider_openrouter_r1()
    await test_agent_db()

if __name__ == "__main__":
    asyncio.run(main()) 