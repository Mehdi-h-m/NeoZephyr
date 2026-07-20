import os
from dotenv import load_dotenv
from typing import Literal
import time
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from neozephyr.tools import AGENT_TOOL, AGENT_FUNCTION,UPDATETASK_FUNCTION,UPDATETASK_TOOL,CREATPLAN_FUNCTION,CREATPLAN_TOOL
import json
from rich.console import Console
from neozephyr.prompts.orchestrator import DEVELOPPER
from neozephyr.models import OrchState
from neozephyr.tools import openai_request_with_retry
import traceback
console=Console()
load_dotenv() 

MODEL="poolside/laguna-xs-2.1:free"
MODEL="openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


TOOLS = [AGENT_TOOL,UPDATETASK_TOOL,CREATPLAN_TOOL]
TOOL_FUNCTIONS = {**AGENT_FUNCTION,**CREATPLAN_FUNCTION,**UPDATETASK_FUNCTION}


def format_Plan(state:OrchState):
    if(state["plan"]):
        plan=f"""Plan :
        Description: {state['plan'].Description}
        Tasks : """
        for task in state["plan"].tasks:
            plan+= f"""
            **{task.id}/ {task.objective}"""
    else :
        plan=f"""Plan : 
        There's no plan yet """
    
    return plan

    

def prompt_user(state: OrchState) -> Command[Literal["LLM", END]] | dict:
    """
    Prompt the user for input and Store it in the state.
    """
    try:
        input_text = console.input(">>")
    except KeyboardInterrupt:    
        input_text = "exit"

    if not ("plan" in state):
        return{ "plan": None,"messages": [{"role": "user", "content": input_text}]} 
    else :
        return{"messages": [{"role": "user", "content": input_text}]}

def call_model(state: OrchState) -> dict:
    with console.status(status="[#2e4a8f]Calling Orchestrator[/#2e4a8f]", spinner="simpleDotsScrolling", spinner_style="#2e4a8f"):
        plantext=format_Plan(state=state)
        time.sleep(1)
        response = openai_request_with_retry(
            client=client,
            model=MODEL,
            messages=[{"role":"developer", "content": DEVELOPPER}] + state["messages"]+[{"role": "user", "content": plantext}],
            tools=TOOLS
        )
        reply = response.choices[0].message
        if(reply.content):
            print()
            console.print(reply.content,style="#2e4a8f")
            print()
        return {"messages": [{
            "role": "assistant",
            "content": reply.content,
            "tool_calls": [tc.model_dump() for tc in reply.tool_calls] if reply.tool_calls else [],
        }]}




def run_tools(state: OrchState) -> dict:
    tool_messages = []
    with console.status(status="[#2e4a8f]Running tools[/#2e4a8f]", spinner="simpleDotsScrolling", spinner_style="#2e4a8f"):

        for call in state["messages"][-1].get("tool_calls", []):

            tool_call_id = call["id"]

            # ---------------- Parse tool call ----------------

            try:
                name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])

            except Exception:
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": (
                            "Tool call could not be parsed.\n\n"
                            f"{traceback.format_exc()}"
                        ),
                    }
                )
                continue

            # print(f"Running tool: {name} with arguments: {args}")

            # ---------------- Find tool ----------------

            if name not in TOOL_FUNCTIONS:

                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": f"Unknown tool '{name}'.",
                    }
                )
                continue

            # ---------------- Execute tool ----------------

            try:
                args["state"]=state
                output = TOOL_FUNCTIONS[name](**args)

                if(name == "call_agent"):
                    tool_messages.append({"role": "tool", "tool_call_id": call["id"], "content": str(output["result"])})
                else:
                    tool_messages.append({"role": "tool", "tool_call_id": call["id"], "content": str(output)})
                if isinstance(output,Command):
                    return output

            except Exception as e:
                # Print locally for debugging
                traceback.print_exc()

                # Return the error to the LLM so it can recover
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": (
                            f"Tool '{name}' failed.\n\n"
                            f"Error type: {type(e).__name__}\n"
                            f"Error: {e}\n\n"
                            f"Traceback:\n{traceback.format_exc()}"
                        ),
                    }
                )

        return {"messages": tool_messages}





def should_continue(state: OrchState) -> str:
    return "TOOLS" if state["messages"][-1].get("tool_calls") else "USER"

def should_stop(state: OrchState) -> str:
        if(state["messages"][-1].get("content").strip().lower() in ["exit", "quit"]):
             print("\nExiting...")
             return END
        return "LLM"

def Orchestrator():
    graph = StateGraph(OrchState)
    graph.add_node("USER", prompt_user)
    graph.add_node("LLM", call_model)
    graph.add_node("TOOLS", run_tools)

    graph.add_edge(START, "USER")
    graph.add_edge("TOOLS", "LLM")

    graph.add_conditional_edges("LLM", should_continue)
    graph.add_conditional_edges("USER", should_stop)
    app = graph.compile()
    result= app.invoke({})

if (__name__ == "__main__"):
    Orchestrator()
