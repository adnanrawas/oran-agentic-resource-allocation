from typing import List, TypedDict, Dict
import aiohttp
import asyncio

class AgentState(TypedDict):
    name: str
    metrics: List[Dict[str, float]]
    counter: int
    trace: [] 


 # Mimic of the mock API response



async def get_metrics():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://master:5000/radio-metrics") as response:
            return await response.json()

############################################################

# async def main():

#     for i in range(3):  # three iterations
#         state: AgentState = {
#             "name": "Agent1",
#             "metrics": [],
#             "counter": 0
#         }
#         data = await get_metrics()

#         state["metrics"].append(data)
#         state["counter"] += 1

#         print("Iteration:", state["counter"])
#         print("Metrics:", data)


#         if data["prb"] > 40:
#             print("Configuration OK")
#             break

#         else:
#             print("Configuration BAD")
    

# asyncio.run(main())