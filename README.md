# NeoZephyre

NeoZephyre is a coding/general-use agent similar to Claude Code and Codex. It currently implements a simple **ReAct (Reason + Act)** loop with 4 tools:

- **Write** — write content to a file
- **Read** — read the content of a file
- **Bash** — execute bash commands
- **Glob** — search the filesystem by file patterns

## Getting Started

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

Get an API key from [openrouter.ai](https://openrouter.ai) and paste it into a `.env` file.

### 5. Run the agent

```bash
python main.py
```
