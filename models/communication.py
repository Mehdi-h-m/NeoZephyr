import operator
from pydantic import BaseModel,Field
from typing import Annotated, Annotated, Literal, TypedDict,Any

class Task(BaseModel):
    id: int= Field(default=0,description="Unique identifier for the task inside the plan(0 position in the plan).")

    type: Literal["code", "research"] = Field(default="",description="The type of the task to be executed wether by code or research agents.")
   
    status: Literal["pending","completed"]= Field(default="pending", description="The status of the task either finished or not yet")
    
    objective: str = Field(default="",description="The objective of the task.")

    context: dict = Field(default={},description="The context for the task that will be known by the other agents.")


class Plan(BaseModel):
    tasks: list[Task]
    Description: str =Field(default="", description="Description of the goal of this Plan")
    id: int= Field(default=0, description="Unique Id of the plan to (incrementing from 0)")


class AgentResult(BaseModel):
    status: Literal[
        "success",
        "failed",
        "need_search",
        "need_code",
        "need_user"
    ] = Field(description="Indicates the status of the agent's operation. It can be 'success', 'failed', 'need_search', 'need_code', or 'need_user'.")

    summary: str= Field(description="A brief summary of the agent's operation or findings.")

    modified_files: list[str] = Field(description="A list of file paths that were modified during the agent's operation.")

    output: list[dict[str, Any]] = Field(
        description="A list of key-value pairs containing additional output or results."
    )

class AgentState(TypedDict):    
    task: Task
    messages: Annotated[list[dict], operator.add]
    result: AgentResult | None

class OrchState(TypedDict):
    messages: Annotated[list[dict], operator.add]
    plan : Plan = Field(default=None)
