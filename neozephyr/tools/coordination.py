from subprocess import run
from enum import Enum
from neozephyr.models import Task,Plan,AgentResult,OrchState
from typing import Literal
from pydantic import BaseModel,Field
from langgraph.types import Command
import json

AGENT_TOOL = {
  "type": "function",
  "function":{
    "name": "call_agent",
    "description": "Delegate a task to another agent and wait for its completion.",
    "parameters": {
      "type": "object",
      "properties": {
        "agent": {
          "type": "string",
          "enum": [
            "coder",
            "researcher"
          ],
          "description": "The agent responsible for the task."
        },
        "task_id": {
          "type": "integer",
          "description": "The Id of the task to execute (starting from 0)."
        },
        "context":{
            "type": "object",
            "description": "The context needed by the agent to execute the task"
        }
      },
      "required": [
        "agent",
        "task_id"
      ],
      "additionalProperties": False
    }
      ,"strict": True
  }
}

FINISH_RESULT_TOOL = {
    "type": "function",
    "function": {
        "name": "finishResult",
        "description": "Call this tool when the task is complete or has come to an end state. This function saves the final summary, status, and modified files.",
        "parameters": AgentResult.model_json_schema(),
        "strict": True
    }
}


CREATPLAN_TOOL={
  "type": "function",
  "function":{
    "name": "create_plan",
    "description": "Create a new execution plan from a high-level task list. Each task should be atomic and executable by either the coding agent or the research agent, This can also be used to change the current Plan",
    "parameters": {
      "type": "object",
      "properties": {
        "description": {
          "type": "string",
          "description": "A short description of the overall goal of the plan."
        },
        "tasks": {
          "type": "array",
          "description": "The ordered list of tasks required to accomplish the goal.",
          "items": {
            "type": "object",
            "properties": {
              "type": {
                "type": "string",
                "enum": [
                  "code",
                  "research"
                ],
                "description": "The type of agent that should execute the task."
              },
              "objective": {
                "type": "string",
                "description": "A clear, specific objective for this task."
              }
            },
            "required": [
              "type",
              "objective"
            ],
            "additionalProperties": False
          },
          "strict": True
        }
      },
      "required": [
        "description",
        "tasks"
      ],
      "additionalProperties": False
    }
    ,"strict": True
  }
} 

UPDATETASK_TOOL={
  "type": "function",
  "function":{
    "name": "change_task_status",
    "description": "Update the execution status of a task in the current plan. Use this after a task starts, completes successfully, or fails.",
    "parameters": {
      "type": "object",
      "properties": {
        "task_id": {
          "type": "integer",
          "description": "The ID of the task to update."
        },
        "status": {
          "type": "string",
          "description": "The new status of the task.",
          "enum": [
            "pending",
            "completed",
          ]
        }
      },
      "required": [
        "task_id",
        "status"
      ],
      "additionalProperties": False
    }
    ,"strict": True
  }
}
class AgentType(str, Enum):
    CODER = "coder"
    RESEARCHER = "researcher"



def call_agent(
    agent: AgentType,
    task_id : int,
    state: OrchState,
    context: dict = {},
):
    
    """
    Invoke a sub-agent and return its final result.
    """
    from neozephyr.agents.coder import Coder
    from neozephyr.agents.searcher import Searcher
    task=state["plan"].tasks[task_id]

    AGENT = {
    AgentType.CODER: Coder,
    AgentType.RESEARCHER: Searcher,
    }
    graph = AGENT[agent]
    task.context=context

    state = {
        "task": task,
        "messages": [],
        "result": None,
    }

    final_state = graph(state)

    return final_state

class MinimalTask(BaseModel):
    
    type: Literal["code", "research"] = Field(default="",description="The type of the task to be executed wether by code or research agents.")

    objective: str = Field(default="",description="The objective of the task.")

def create_plan(
    tasks: list[MinimalTask],
    description: str,
    state: OrchState
) -> Plan|Command:

    complete_tasks = []

    for i, task in enumerate(tasks):
        if isinstance(task, dict):
            task = MinimalTask.model_validate(task)
        complete_tasks.append(
            Task(
                id=i,
                type=task.type,
                objective=task.objective,
                context={},
            )
        )
    plan=Plan(
        tasks=complete_tasks,
        description=description,
     )
    
    #TO ADD SERIALIZATION OF THE PLAN
    return Command(
        update={
            "plan": plan
        }
    )



def change_task_status(
    task_id: int,
    status: Literal["pending","completed"],
    state: OrchState
) -> Plan:
    """
    Change the status of a task inside a plan.

    Args:
        plan: The execution plan.
        task_id: ID of the task.
        status: New status.

    Returns:
        The updated plan.

    Raises:
        ValueError: If the task ID does not exist.
    """
    plan=state["plan"]
    for task in plan.tasks:
        if task.id == task_id:
            task.status = status
            state["plan"]=plan
            return Command(
              update={
                 "plan": plan
                   }
             )

    raise ValueError(f"Task {task_id} not found.")

def execute_finish_result(
    status: str,
    summary: str,
    modified_files: list[str],
    output: list[dict[str, str]],
) -> AgentResult:
    return AgentResult(
        status=status,
        summary=summary,
        modified_files=modified_files,
        output=output,
    )

CREATPLAN_FUNCTION={"create_plan":create_plan}
AGENT_FUNCTION={"call_agent":call_agent}
UPDATETASK_FUNCTION={"change_task_status":change_task_status}
FINISH_RESULT_FUNCTION={"finishResult": execute_finish_result}
