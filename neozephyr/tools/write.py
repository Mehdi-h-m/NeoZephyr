import os
import subprocess
import platform

EDIT_TOOL ={
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file, creating it if needed or overwriting if it exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to edit"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
                "additionalProperties": False
            },
        "strict": True
        },
    }
BASH_TOOL = {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command and return stdout/stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                },
                "required": ["command"],
                "additionalProperties": False
            },
        "strict": True
        },
    }

def write(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"

def bash(command: str) -> str:
    try:
        if platform.system() == "Windows":
            cmd = ["powershell", "-NoProfile", "-Command", command]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30s"
    except Exception as e:
        return f"Error running command: {e}"

EDIT_FUNCTION = write
BASH_FUNCTION = bash