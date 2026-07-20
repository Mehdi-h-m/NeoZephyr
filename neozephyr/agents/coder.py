import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from neozephyr.models.communication import AgentState,Task
from neozephyr.tools import EDIT_FUNCTION, READ_FUNCTION, EDIT_TOOL, READ_TOOL,BASH_TOOL, BASH_FUNCTION,FINISH_RESULT_TOOL,FINISH_RESULT_FUNCTION
from neozephyr.prompts.coder import DEVELOPPER
import time
from neozephyr.tools import openai_request_with_retry
import traceback
from rich.console import Console

load_dotenv() 
console = Console()
# MODEL="poolside/laguna-xs-2.1:free"
MODEL="openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

TOOLS = [EDIT_TOOL, READ_TOOL, BASH_TOOL,FINISH_RESULT_TOOL]
TOOLS_FUNCTIONS = {**EDIT_FUNCTION, **READ_FUNCTION, **BASH_FUNCTION, **FINISH_RESULT_FUNCTION}

import os
import platform


def code(state: AgentState):
    with console.status(status="[#fe9c00]Calling Coder[/#fe9c00]", spinner="simpleDotsScrolling", spinner_style="#fe9c00"):
        if isinstance(state["task"], Task):
            task = state["task"]
        else:
            task = Task.model_validate_json(state["task"])
        time.sleep(1)
        response = openai_request_with_retry(
        client=client,
        model=MODEL,
        messages=[{"role":"developer", "content": DEVELOPPER}, *state["messages"],{"role": "user", "content": f""" Task: {task.objective} Context: {task.context}"""}],
        tools=TOOLS,
        )
        reply = response.choices[0].message
        if(reply.content):
            print()
            console.print(reply.content,style="#fe9c00")
            print()
        return {
            "messages": [{
                "role": "assistant",
                "result": response.choices[0].message.content,
                "tool_calls": [tc.model_dump() for tc in response.choices[0].message.tool_calls] if response.choices[0].message.tool_calls else [],
            }]
        }


def run_tools(state: AgentState) -> dict:
    tool_messages = []
    with console.status(status="[#fe9c00]Coder Running tools[/#fe9c00]", spinner="simpleDotsScrolling", spinner_style="#fe9c00"):
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
        console.print("Coder called tools",style="#fe9c00")
        return {"messages": tool_messages}


def finish(state:AgentState):
    with console.status(status="[#fe9c00]Coder Finishing[/#fe9c00]", spinner="simpleDotsScrolling", spinner_style="#fe9c00"):
        call=state["messages"][-1].get("tool_calls", [])[0]
        name = call["function"]["name"]
        args = json.loads(call["function"]["arguments"])
        output = TOOLS_FUNCTIONS[name](**args)
        result={"role": "tool", "tool_call_id": call["id"], "content": str(output)}
        console.print("Coder Finished",style="#fe9c00")
        return {"messages": [result],"result":output}




def should_continue(state: AgentState) -> str:
    if not (state["messages"][-1].get("tool_calls")):
        return "FORCETOOL"
    if state["messages"][-1].get("tool_calls")[0]["function"]["name"]=="finishResult":
        return "FINISH"
    return "TOOLS"

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
    return {
        "messages": [{
            "role": "tool",
            "result": response.choices[0].message.content,
            "tool_calls": [tc.model_dump() for tc in response.choices[0].message.tool_calls] if response.choices[0].message.tool_calls else [],
        }]
    }


def Coder(state:AgentState={}):
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
    Coder()
