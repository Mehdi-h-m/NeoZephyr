import os
from dotenv import load_dotenv
from typing import Literal
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from neozephyr.tools import TOOLS
from rich.console import Console
from neozephyr.agents import Worker
from neozephyr.prompts import ORCHDEVELOPPER,PLANNERDEVELOPPER
from neozephyr.models import OrchestratorOutput,OrchState,PlannerOutput,ExecutionResult,Plan,Task,AgentResult
from neozephyr.tools import openai_request_with_retry,toolforce, ORCHESTRATOR_DECISION_TOOL, CREATE_PLAN_TOOL

console=Console()
load_dotenv() 

MODEL="poolside/laguna-xs-2.1:free"
MODEL="openrouter/free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def format_Plan(state:OrchState):
    if(state["plan"]):
        plan=f"""Plan :
        PlanID : {state['plan'].id}
        Description: {state['plan'].description}
        Tasks : """
        for task in state["plan"].plan:
            plan+= f"""
            ** ID:{task.id}/ {task.objective}"""
    else :
        plan=f"""Plan : 
        There's no plan yet """
    
    return plan


def format_execution_history(state: OrchState) -> str:
    if not state.get("execution_history") :
        return """Execution History:
There is no execution history yet."""

    history = "Execution History:\n"

    for execution in state["executionHistory"]:
        history += f"""
----------------------------------------
Plan ID: {execution.plan_id}
Task ID: {execution.task_id}
Status: {execution.result.status}
Summary: {execution.result.summary}"""

        if execution.result.modified_files:
            history += "\nModified Files:"
            for file in execution.result.modified_files:
                history += f"\n- {file}"

        if execution.result.output:
            history += "\nOutput:"
            for item in execution.result.output:
                history += f"\n- {item}"

        history += "\n"

    return history






def prompt_user(state: OrchState) -> Command[Literal["ORCHESTRATOR", END]] | dict:
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
        plantext = f"""
        {format_Plan(state)}

        {format_execution_history(state)}
        """
        response = toolforce(
            tool_name="orchestratorDecision",
            client=client,
            model=MODEL,
            messages=[{"role":"developer", "content": ORCHDEVELOPPER}] + state["messages"]+[{"role": "user", "content": plantext}],
            tools=[ORCHESTRATOR_DECISION_TOOL],
            tool_choice={
                "type": "function",
                "function": {
                    "name": "orchestratorDecision"
                }
            }
        )
        reply = response.choices[0].message
        result = OrchestratorOutput(
            action="finish",      # temporary default
            user_output="",
            task_id=None,
            context={},
        )

        call = reply.tool_calls[0]

        result = OrchestratorOutput.model_validate(
            call.function.parsed_arguments)

        if result.user_output:
            console.print()
            console.print(result.user_output, style="#2e4a8f")
            console.print()

        return {
            "messages": [{
                "role": "assistant",
                "content": result.user_output,
                "tool_calls": [
                    tc.model_dump() for tc in reply.tool_calls
                ] if reply.tool_calls else [],
            }],
            "action": result.action,
            "current_task_id": result.task_id,
            "current_context": result.context
        }
    

def plan(state: OrchState):
      
    with console.status(status="[#2e4a8f]Calling Planner[/#2e4a8f]", spinner="simpleDotsScrolling", spinner_style="#2e4a8f"):
        available_tools = "\n".join(
        f"- {tool['function']['name']}: {tool['function']['description']}"
        for tool in TOOLS.definitions()
        )

        plantext = f"""
        {format_Plan(state)}

        {format_execution_history(state)}

        Available Worker Tools
        ======================

        The planner may assign any subset of the following tools to each task.

        {available_tools}
        """
        response = toolforce(
            tool_name="createPlan",
            client=client,
            model=MODEL,
            messages=[{"role":"developer", "content": PLANNERDEVELOPPER}] + state["messages"]+[{"role": "user", "content": plantext}],
            tools=[CREATE_PLAN_TOOL],
            tool_choice={
                "type": "function",
                "function": {
                    "name": "createPlan"
                }
            }
        )
        reply = response.choices[0].message
        result = PlannerOutput(
            plan= None
        )
        call = reply.tool_calls[0]

        result = PlannerOutput.model_validate(
            call.function.parsed_arguments)

        if(state["plan"]):
            next_plan_id = state["plan"].id +1
        else:
                next_plan_id=0

    return {"plan":Plan(
        id=next_plan_id,
        description=result.plan.description,
        plan=[
            Task(
                id=i,
                **task.model_dump(),
             )
        for i, task in enumerate(result.plan.tasks)
         ],
    )
    }

def run_agent(state:OrchState):
    planID=state["plan"].id
    taskID=state["current_task_id"]
    task= state["plan"].plan[taskID]
    task.context=state["current_context"]
    work= Worker({"task": task})
    result = work.result
    state["plan"].plan[taskID].status = "completed"
    executionresult= ExecutionResult(result=result,planID=planID,taskID=taskID)
    return{
        "execution_history": executionresult,
        "current_task_id" : None,
        "current_context" : ""
    }



def should_continue(state: OrchState) -> str:
    match state["action"]:
        case "finish":
            return "USER"
        case "run_task":
            return "AGENT"
        case "create_plan":
            return "PLANNER"
        case "replan":
            return "PLANNER"
    

def should_stop(state: OrchState) -> str:
        if(state["messages"][-1].get("content").strip().lower() in ["exit", "quit"]):
             print("\nExiting...")
             return END
        return "ORCHESTRATOR"

def Orchestrator():
    graph = StateGraph(OrchState)
    graph.add_node("USER", prompt_user)
    graph.add_node("ORCHESTRATOR", call_model)
    graph.add_node("AGENT", run_agent)
    graph.add_node("PLANNER",plan)

    graph.add_edge(START, "USER")
    graph.add_edge("PLANNER", "ORCHESTRATOR")
    graph.add_edge("AGENT","ORCHESTRATOR")

    graph.add_conditional_edges("ORCHESTRATOR", should_continue)
    graph.add_conditional_edges("USER", should_stop)
    app = graph.compile()
    result= app.invoke({})

if (__name__ == "__main__"):
    Orchestrator()
