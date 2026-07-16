
import os
from dotenv import load_dotenv
from typing import Literal, TypedDict, Annotated, Union
import operator
import time
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from tools import TOOLS,TOOL_FUNCTIONS
import json
from rich.console import Console
from rich.prompt import Prompt


console=Console()
load_dotenv() 

# MODEL="poolside/laguna-xs-2.1:free"
MODEL="openrouter/free"
DEVELOPPER=f"you are a helpful assistant working at {os.getcwd()} in a windows operating system that can read and write files, execute shell commands via PowerShell, and find files matching glob patterns. You are able to use the following tools: read, write, bash, glob. You are able to use these tools to help the user accomplish their goals. You should always try to use these tools when appropriate. You should never make up information or hallucinate. You should always be honest about what you know and what you don't know. You should always ask the user for clarification if you are unsure about what they want. You should always try to be helpful and provide useful information to the user."

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]

def prompt_user(state: AgentState) -> Command[Literal["LLM", END]] | dict:
    """
    Prompt the user for input and Store it in the state.
    """
    try:
        input_text = console.input(">>")
    except KeyboardInterrupt:    
        input_text = "exit"
    return{ "messages": [{"role": "user", "content": input_text}]} 

def call_model(state: AgentState) -> dict:
    print("Calling model...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"developer", "content": DEVELOPPER}] + state["messages"],
        tools=TOOLS
    )
    reply = response.choices[0].message
    print(reply.content)
    return {"messages": [{
        "role": "assistant",
        "content": reply.content,
        "tool_calls": [tc.model_dump() for tc in reply.tool_calls] if reply.tool_calls else [],
    }]}

def run_tools(state: AgentState) -> dict:
    results = []
    print("Running tools...")
    for call in state["messages"][-1].get("tool_calls", []):
        name = call["function"]["name"]
        args = json.loads(call["function"]["arguments"])
        print(f"Running tool: {name} with arguments: {call['function']['arguments']}")
        output = TOOL_FUNCTIONS[name](**args)
        results.append({"role": "tool", "tool_call_id": call["id"], "content": str(output)})
    return {"messages": results}

def should_continue(state: AgentState) -> str:
    return "LLM" if state["messages"][-1].get("role") == "tool" else "USER"

def should_stop(state: AgentState) -> str:
        if(state["messages"][-1].get("content").strip().lower() in ["exit", "quit"]):
             print("\nExiting...")
             return END
        return "LLM"

def Orchestrator():
    graph = StateGraph(AgentState)
    graph.add_node("USER", prompt_user)
    graph.add_node("LLM", call_model)
    graph.add_node("TOOLS", run_tools)

    graph.add_edge(START, "USER")
    graph.add_edge("LLM", "TOOLS")

    graph.add_conditional_edges("TOOLS", should_continue)
    graph.add_conditional_edges("USER", should_stop)
    app = graph.compile()
    result= app.invoke({})

if (__name__ == "__main__"):
    Orchestrator()