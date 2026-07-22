from subprocess import run
from enum import Enum
from neozephyr.models import AgentResult,OrchestratorOutput,PlannerOutput
from pydantic import BaseModel


def create_virtual_tool(
    *,
    name: str,
    description: str,
    model: type[BaseModel],
) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": (
                description
                + " Call this function exactly once. "
            ),
            "parameters": model.model_json_schema(),
            "strict": True,
        },
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

ORCHESTRATOR_DECISION_TOOL = create_virtual_tool(
    name="orchestratorDecision",
    description="Return the next orchestration decision.",
    model=OrchestratorOutput,
)

CREATE_PLAN_TOOL = create_virtual_tool(
    name="createPlan",
    description="Generate an execution plan for the user's objective.",
    model=PlannerOutput,
)

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

FINISH_RESULT_FUNCTION= execute_finish_result
