from langgraph.graph import StateGraph
import os
import glob as glob_module
from pathlib import Path
from subprocess import run
from pydantic import BaseModel

READ_TOOL =     {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"},
                },
                "required": ["path"],
                "additionalProperties": False
            },
        "strict": True
        },
    }

GLOB_TOOL = {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files matching a glob pattern, e.g. '**/*.py'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern to match"},
                    "path": {"type": "string", "description": "Directory to search from (default: cwd)"},
                },
                "required": ["pattern"],
                "additionalProperties": False
            },
        "strict": True
        },
    }

GREP_TOOL={
  "type": "function",
  "function":{
    "name": "search_code",
    "description": "Search for text or regular expressions inside the project using ripgrep. Returns matching files and line numbers.",
    "parameters": {
        "type": "object",
        "properties": {
        "query": {
            "type": "string",
            "description": "The text or regular expression to search for."
        },
        "file_pattern": {
            "type": "string",
            "description": "Optional glob pattern such as '*.py' or '*.js'."
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of matches to return.",
            "default": 50
        }
        },
        "required": [
        "query"
        ],
        "additionalProperties": False
    },
    "strict": True
  }
}

def read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"
    
def glob(pattern: str, path: str = ".") -> str:
    matches = glob_module.glob(os.path.join(path, pattern), recursive=True)
    return "\n".join(matches) if matches else "No files matched"

class GrepMatch(BaseModel):
    file: str
    line: int
    column: int
    text: str


def search_code(
    query: str,
    directory: str | Path = ".",
    file_pattern: str | None = None,
    max_results: int = 50,
    case_sensitive: bool = False,
) -> list[GrepMatch]:
    """
    Search source code using ripgrep.

    Args:
        query: Text or regex to search for.
        directory: Root directory to search.
        file_pattern: Optional glob pattern (e.g. "*.py").
        max_results: Maximum number of matches returned.
        case_sensitive: Whether the search should be case-sensitive.

    Returns:
        List of GrepMatch objects.
    """

    command = [
        "rg",
        "--line-number",
        "--column",
        "--with-filename",
        "--max-count",
        str(max_results),
    ]

    if not case_sensitive:
        command.append("-i")

    if file_pattern:
        command.extend(["-g", file_pattern])

    command.extend([query, str(directory)])

    try:
        result = run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError:
        raise RuntimeError(
            "ripgrep (rg) is not installed. Install it from https://github.com/BurntSushi/ripgrep"
        )

    # rg returns:
    # 0 -> matches found
    # 1 -> no matches
    # >1 -> error
    if result.returncode > 1:
        raise RuntimeError(result.stderr.strip())

    matches: list[GrepMatch] = []
    stdout = result.stdout or ""

    for line in stdout.splitlines():

        try:
            file, line_no, column, text = line.split(":", 3)

            matches.append(
                GrepMatch(
                    file=file,
                    line=int(line_no),
                    column=int(column),
                    text=text,
                )
            )

        except ValueError:
            # Ignore malformed lines
            continue

    return matches

READ_FUNCTION = {"read": read}
GLOB_FUNCTION = {"glob": glob}
GREP_FUNCTION = {"search_code": search_code}