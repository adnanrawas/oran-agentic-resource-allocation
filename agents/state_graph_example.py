# import operator
# from typing import TypedDict
# from typing_extensions import Annotated
# from langgraph.graph import StateGraph, END


# # Define our state
# class State(TypedDict):
#     messages: Annotated[list, operator.add]
#     location: str
#     weather: str


# # Create our graph
# workflow = StateGraph(State)


# # Define our nodes
# def greet(state):
#     return {"messages": [("ai", "Hello! I'm your weather assistant. Where are you located?")]}


# def get_location(state):
#     return {"location": state["messages"][-1][1]}


# def check_weather(state):
#     # In a real app, we'd call a weather API here
#     weather = "sunny" if "new york" in state["location"].lower() else "rainy"
#     return {"weather": weather}


# def report_weather(state):
#     return {"messages": [
#         ("ai", f"The weather in {state['location']} is {state['weather']}. Can I help you with anything else?")]}


# # Add nodes to our graph
# workflow.add_node("greet", greet)
# workflow.add_node("get_location", get_location)
# workflow.add_node("check_weather", check_weather)
# workflow.add_node("report_weather", report_weather)

# # Connect our nodes
# workflow.set_entry_point("greet")
# workflow.add_edge("greet", "get_location")
# workflow.add_edge("get_location", "check_weather")
# workflow.add_edge("check_weather", "report_weather")
# workflow.add_edge("report_weather", END)

# # Compile our graph
# app = workflow.compile()

# # Run our app
# inputs = {"messages": [("human", "Hi, I'd like to check the weather.")]}
# for output in app.stream(inputs):
#     for key, value in output.items():
#         print(f"{key}: {value}")