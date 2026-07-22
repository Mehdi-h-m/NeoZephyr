from pydantic import BaseModel,Field
from typing import Annotated, Annotated, Literal, TypedDict,Any
import operator
from neozephyr.models import AgentResult,Task


class Taskdraft(BaseModel):
        tools: list[str] = Field(
        description=(
            "Names of the tools required to complete this task. "
            "Only include tools that are genuinely needed."
        )
        )
        objective: str = Field(description="A clear, self-contained objective that a worker can complete "
        "without needing additional planning.")



class Plan(BaseModel):
    plan: list[Task]
    id: int= Field(default=0, description="Unique Id of the plan to (incrementing from 0)")
    description: str =Field(description="Description of the goal of this Plan")

class PlanDraft(BaseModel):
    tasks: list[Taskdraft]
    description: str =Field(description="Description of the goal of this Plan")




class OrchestratorOutput(BaseModel):
    action: Literal[
        "create_plan",
        "replan",
        "run_task",
        "finish",
    ] = Field(
    description=(
        "The next action for the orchestration workflow.\n\n"
        "- 'create_plan': Generate an initial execution plan for the user's objective"
        "Choose this when no valid plan currently exists or the previous plan is completed and now a new user request came in.\n\n"
        "- 'replan': generate a new or updated execution plan because the current plan is no longer valid, "
        "Choose this when the agent results or user input changed the context and additional tasks are required"
        "- 'run_task': Execute exactly one pending task from the current plan. "
        "Use this only when the existing plan cannot efficiently achieve the objective.\n\n"
        "- 'finish': if you want to go back to the user , use this if you finished your work or need more information from the user"
    )
    )

    task_id: int | None = Field(
        default=None,
        description=(
            "The unique identifier of the task to execute. "
            "Provide this only when action='run_task'. "
            "It must correspond to a task that exists in the current plan. "
            "Otherwise leave this field null."
        )
    )
    user_output: str = Field(
        default="",
    description=(
        "A user-facing message describing the current state of execution. "
        "Use this field whenever the user should be informed about what is happening, "
        "what is about to happen, important findings, required user actions, or the final outcome. "
        "Leave this field empty only when there is nothing meaningful to communicate to the user."
    )
    )

    context: dict[str, Any] = Field(
        default="",
        description=(
            "Additional context that should be passed to the worker agent executing the selected task. "
            "This is not intended to talk to users only to agents. "
            "Include only information that helps complete THIS task, such as discoveries from previous tasks, "
            "relevant file paths, implementation decisions, constraints, assumptions, or intermediate results. "
            "Do not repeat the entire conversation or the whole execution plan. "
            "If no additional context is required, return an empty dictionary. "
            "If the action field is not 'run_task' return an empty dictionary. "
        )
    )


class PlannerOutput(BaseModel):
    plan: PlanDraft|None = Field(description="The complete new plan of execution")
class OrchState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    plan : Plan = Field(default=None)
    action: Literal["create_plan", "run_task", "finish"]
    execution_history: Annotated[list[ExecutionResult], operator.add]
    current_task_id: int | None
    current_context: dict[str, Any]

class ExecutionResult(BaseModel):
    result: AgentResult
    planID: int
    taskID: int
