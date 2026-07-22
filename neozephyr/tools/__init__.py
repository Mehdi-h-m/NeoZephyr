from .write import EDIT_TOOL, EDIT_FUNCTION,BASH_TOOL, BASH_FUNCTION
from .read import READ_TOOL, READ_FUNCTION, GLOB_TOOL, GLOB_FUNCTION,GREP_FUNCTION,GREP_TOOL
from .coordination import (FINISH_RESULT_FUNCTION,FINISH_RESULT_TOOL,
                           CREATE_PLAN_TOOL,
                           ORCHESTRATOR_DECISION_TOOL)
from .General import openai_request_with_retry,toolforce
from neozephyr.models import ToolRegistry
All = [
    EDIT_TOOL,
    EDIT_FUNCTION,

    BASH_TOOL,
    BASH_FUNCTION,

    READ_TOOL,
    READ_FUNCTION,

    GLOB_TOOL,
    GLOB_FUNCTION,

    GREP_TOOL,
    GREP_FUNCTION,

    FINISH_RESULT_TOOL,
    FINISH_RESULT_FUNCTION
]

TOOLS = ToolRegistry(
    [
        (EDIT_TOOL, EDIT_FUNCTION),
        (BASH_TOOL, BASH_FUNCTION),
        (READ_TOOL, READ_FUNCTION),
        (GLOB_TOOL, GLOB_FUNCTION),
        (GREP_TOOL, GREP_FUNCTION),
    ]
)