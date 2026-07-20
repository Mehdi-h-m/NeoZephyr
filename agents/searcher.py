import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from models.communication import AgentState,AgentResult,Task
from tools import GLOB_FUNCTION, READ_FUNCTION, GLOB_TOOL, READ_TOOL,GREP_TOOL, GREP_FUNCTION,FINISH_RESULT_TOOL,FINISH_RESULT_FUNCTION
from prompts.coder import DEVELOPPER
import time
from tools import openai_request_with_retry
import traceback
load_dotenv() 

MODEL="poolside/laguna-xs-2.1:free"
MODEL="openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

TOOLS = [GLOB_TOOL, READ_TOOL, GREP_TOOL,FINISH_RESULT_TOOL]
TOOLS_FUNCTIONS = {**GLOB_FUNCTION, **READ_FUNCTION, **GREP_FUNCTION,**FINISH_RESULT_FUNCTION}

import os
import platform


def code(state: AgentState):
    print("SEARCHER CALLING.....")
    
    if isinstance(state["task"], Task):
        task = state["task"]
    else:
        task = Task.model_validate_json(state["task"])
    response = openai_request_with_retry(
        client=client,
     model=MODEL,
     messages=[{"role":"developer", "content": DEVELOPPER}, *state["messages"],{"role": "user", "content": f""" Task: {task.objective} Context: {task.context}"""}],
     tools=TOOLS,
     )
    return {
        "messages": [{
            "role": "assistant",
            "result": response.choices[0].message.content,
            "tool_calls": [tc.model_dump() for tc in response.choices[0].message.tool_calls] if response.choices[0].message.tool_calls else [],
        }]
    }


def run_tools(state: AgentState) -> dict:
    tool_messages = []

    print("SEARCHER Running tools...")

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

        print(f"Running tool: {name} with arguments: {args}")

        # ---------------- Find tool ----------------

        if name not in TOOLS_FUNCTIONS:
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
            output = TOOLS_FUNCTIONS[name](**args)

            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(output),
                }
            )

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

def should_continue(state: AgentState) -> str:
    if not (state["messages"][-1].get("tool_calls")):
        return "FORCETOOL"
    if state["messages"][-1].get("tool_calls")[0]["function"]["name"]=="finishResult":
        return "FINISH"
    return "TOOLS"

def finish(state:AgentState):
    print("SEARCHER FINISHING ......")
    call=state["messages"][-1].get("tool_calls", [])[0]
    name = call["function"]["name"]
    args = json.loads(call["function"]["arguments"])
    print(f"Running tool: {name} with arguments: {call['function']['arguments']}")
    output = TOOLS_FUNCTIONS[name](**args)
    result={"role": "tool", "tool_call_id": call["id"], "content": str(output)}
    return {"messages": [result],"result":output}

def force_tool(state:AgentState):
    if isinstance(state["task"], Task):
        task = state["task"]
    else:
        task = Task.model_validate_json(state["task"])
    time.sleep(1)
    response = openai_request_with_retry(
        client=client,
    model=MODEL,
    messages=[{"role":"developer", "content": DEVELOPPER}, *state["messages"],{"role": "user", "content": f""" Task: {task.objective} Context: {task.context} ALERT: IF YOU FINISHED YOUR TASK ALWAYS CALL THE finishResult tool TO REPORT YOUR TASK INFORMATIONS, you always have to call a tool"""}],
   tools=TOOLS,
    )
    reply = response.choices[0].message
    if(reply.content):
         print(reply.content)
    return {
        "messages": [{
            "role": "tool",
            "result": response.choices[0].message.content,
            "tool_calls": [tc.model_dump() for tc in response.choices[0].message.tool_calls] if response.choices[0].message.tool_calls else [],
        }]
    }


def Searcher(state:AgentState={}):
    builder = StateGraph(AgentState)

    builder.add_node("CODER", code)

    builder.add_node("TOOLS", run_tools)

    builder.add_node("FORCETOOL",force_tool)

    builder.add_node("FINISH",finish)

    builder.add_edge(START, "CODER") 

    builder.add_edge("TOOLS", "CODER")

    builder.add_edge("FINISH",END)

    builder.add_conditional_edges("CODER", should_continue)

    builder.add_conditional_edges("FORCETOOL",should_continue)

    coding_graph = builder.compile()

    return coding_graph.invoke(state)

if(__name__ == "__main__"):
    Searcher()