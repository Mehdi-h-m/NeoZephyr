# NeoZephyr

NeoZephyr is a coding/general-use AI agent inspired by tools like Claude Code and Codex. It currently implements a simple **ReAct (Reason + Act)** loop with the following tools:

- **Write** — Write content to a file
- **Read** — Read the contents of a file
- **Bash** — Execute shell commands
- **Glob** — Search the filesystem using file patterns

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd NeoZephyr
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Linux/macOS**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 4. Install the project

Install NeoZephyr in editable mode:

```bash
pip install -e .
```

This installs the `neo` command, allowing you to run NeoZephyr from any directory.

### 5. Set up your API key

Create a `.env` file in the project root and add your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_api_key_here
```

You can obtain an API key from https://openrouter.ai.

## Usage

Start NeoZephyr from any directory by running:

```bash
neo
```