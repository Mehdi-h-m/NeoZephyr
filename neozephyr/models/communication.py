import operator
from pydantic import BaseModel,Field
from typing import Annotated, Annotated, Literal, TypedDict,Any

class AgentResult(BaseModel):
    status: Literal[
        "success",
        "failed",
        "need_tools",
        "need_user"
    ] = Field(description=("Indicates the status of the agent's operation. It can be : \n\n"
         "-success : if the task completed successfully\n", 
         "-failed : if it is impossible to execute the task\n",
        "-need_tools: if the tools given are not enough to execute the task\n",
        "-need_user: if context from user is needed ,like confirmation or context\n"))

    summary: str= Field(description="A brief summary of the agent's operation or findings.")

    modified_files: list[str] = Field(description="A list of file paths that were modified during the agent's operation.")

    output: list[dict[str, Any]] = Field(
        description="A list of key-value pairs containing additional output or results."
    )

class AgentState(TypedDict):    
    task: Task
    messages: Annotated[list[dict], operator.add]
    result: AgentResult | None

class Task(BaseModel):
    id: int= Field(default=0,description="Unique identifier for the task inside the plan(0 position in the plan).")

    tools: list[str] = Field(
        description=(
            "Names of the tools required to complete this task. "
            "Only include tools that are genuinely needed."
        )
    )
   
    status: Literal["pending","completed"]= Field(default="pending", description="The status of the task either finished or not yet")
    
    objective: str = Field(default="",description="A clear, self-contained objective that a worker can complete "
            "without needing additional planning.")

    context: dict[str, Any] = Field(default={},description="The context for the task that will be known by the other agents.")
