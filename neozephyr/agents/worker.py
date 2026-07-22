import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from neozephyr.models.communication import AgentState,Task
from neozephyr.tools import TOOLS, FINISH_RESULT_FUNCTION,FINISH_RESULT_TOOL
from neozephyr.prompts.worker import DEVELOPPER
from neozephyr.tools import toolforce
import traceback
from rich.console import Console

console= Console()
load_dotenv() 

MODEL="poolside/laguna-xs-2.1:free"
MODEL="openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
import os


def call(state: AgentState):

    with console.status(status="[#ff8c00]Calling Worker[/#ff8c00]", spinner="simpleDotsScrolling", spinner_style="#ff8c00"):
        
        if isinstance(state["task"], Task):
            task = state["task"]
            WORKERTOOLS=TOOLS.subset(task.tools)
        else:
            task = Task.model_validate_json(state["task"])
            WORKERTOOLS=TOOLS.subset(task.tools)
        response = toolforce(
            client=client,
        model=MODEL,
        messages=[{"role":"developer", "content": DEVELOPPER}, *state["messages"],{"role": "user", "content": f""" Task: {task.objective} Context: {task.context}"""}],
        tools=WORKERTOOLS.definitions()+[FINISH_RESULT_TOOL],
        )
        reply = response.choices[0].message
        if(reply.content):
            print()
            console.print(reply.content,style="#ff8c00")
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
    with console.status(status="[#ff8c00]Worker Running tools[/#ff8c00]", spinner="simpleDotsScrolling", spinner_style="#ff8c00"):

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
            if isinstance(state["task"], Task):
              task = state["task"]
              WORKERTOOLS=TOOLS.subset(task.tools)
            else:
                task = Task.model_validate_json(state["task"])
                WORKERTOOLS=TOOLS.subset(task.tools)
            if not TOOLS.exists(name):
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
                output = WORKERTOOLS.function(name)(**args)

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
        console.print("Worker called tools",style="#ff8c00")
        return {"messages": tool_messages}

def should_continue(state: AgentState) -> str:
    if not (state["messages"][-1].get("tool_calls")):
        return "WORKER"
    if state["messages"][-1].get("tool_calls")[0]["function"]["name"]=="finishResult":
        return "FINISH"
    return "TOOLS"

def finish(state:AgentState):
    with console.status(status="[#ff8c00]Worker Finishing[/#ff8c00]", spinner="simpleDotsScrolling", spinner_style="#ff8c00"):
        call=state["messages"][-1].get("tool_calls", [])[0]
        args = json.loads(call["function"]["arguments"])
        output = FINISH_RESULT_FUNCTION(**args)
        result={"role": "tool", "tool_call_id": call["id"], "content": str(output)}
        console.print("Worker finished work",style="#ff8c00")
        return {"messages": [result],"result":output}


def Worker(state:AgentState={}):
    builder = StateGraph(AgentState)

    builder.add_node("WORKER", call)

    builder.add_node("TOOLS", run_tools)

    builder.add_node("FINISH",finish)

    builder.add_edge(START, "WORKER") 

    builder.add_edge("TOOLS", "WORKER")

    builder.add_edge("FINISH",END)

    builder.add_conditional_edges("WORKER", should_continue)

    coding_graph = builder.compile()

    return coding_graph.invoke(state)

if(__name__ == "__main__"):
    Worker()
