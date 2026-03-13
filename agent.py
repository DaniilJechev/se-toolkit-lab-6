#!/usr/bin/env python3
"""
Learning Management Service Agent

A CLI tool that answers questions using an LLM with tool calling.
Usage: uv run agent.py "Your question here"

Tools:
- read_file: Read contents of a file
- list_files: List files in a directory
"""

import json
import os
import sys
from pathlib import Path

import httpx


# Maximum number of tool calls per question
MAX_TOOL_CALLS = 10


def load_env(env_path: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def load_config() -> dict[str, str]:
    """Load LLM configuration from .env.agent.secret."""
    project_root = Path(__file__).parent
    env_path = project_root / ".env.agent.secret"

    config = load_env(env_path)

    required_keys = ["LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL"]
    missing = [key for key in required_keys if key not in config]

    if missing:
        print(f"Error: Missing required config keys: {missing}", file=sys.stderr)
        print("Please create .env.agent.secret with required values.", file=sys.stderr)
        sys.exit(1)

    return config


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def validate_path(path: str) -> tuple[bool, str]:
    """
    Validate that a path is within the project directory.
    Returns (is_valid, error_message).
    """
    # Check for directory traversal
    if ".." in path:
        return False, "Error: Path traversal not allowed"

    # Resolve to absolute path
    project_root = get_project_root()
    try:
        full_path = (project_root / path).resolve()
        # Check if the resolved path is within project root
        if not str(full_path).startswith(str(project_root.resolve())):
            return False, "Error: Path outside project directory"
        return True, ""
    except Exception as e:
        return False, f"Error: Invalid path - {e}"


def read_file(path: str) -> str:
    """
    Read the contents of a file.

    Args:
        path: Relative path from project root

    Returns:
        File contents as string, or error message
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return error

    project_root = get_project_root()
    file_path = project_root / path

    if not file_path.exists():
        return f"Error: File not found: {path}"

    if not file_path.is_file():
        return f"Error: Not a file: {path}"

    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str) -> str:
    """
    List files and directories at a given path.

    Args:
        path: Relative directory path from project root

    Returns:
        Newline-separated listing of entries, or error message
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return error

    project_root = get_project_root()
    dir_path = project_root / path

    if not dir_path.exists():
        return f"Error: Directory not found: {path}"

    if not dir_path.is_dir():
        return f"Error: Not a directory: {path}"

    try:
        entries = list(dir_path.iterdir())
        # Sort: directories first, then files
        entries.sort(key=lambda x: (not x.is_dir(), x.name))
        return "\n".join([e.name for e in entries])
    except Exception as e:
        return f"Error listing directory: {e}"


# Tool definitions
TOOLS = {
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the project repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    "list_files": {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path in the project repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki', 'plans')"
                    }
                },
                "required": ["path"]
            }
        }
    }
}

# Map tool names to functions
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files
}


def get_tool_definitions() -> list[dict]:
    """Get tool definitions for the LLM API."""
    return list(TOOLS.values())


def execute_tool(tool_name: str, args: dict) -> str:
    """
    Execute a tool and return the result.

    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool

    Returns:
        Tool result as string
    """
    if tool_name not in TOOL_FUNCTIONS:
        return f"Error: Unknown tool: {tool_name}"

    func = TOOL_FUNCTIONS[tool_name]

    # Extract arguments
    if tool_name == "read_file":
        path = args.get("path", "")
        return func(path)
    elif tool_name == "list_files":
        path = args.get("path", "")
        return func(path)

    return f"Error: Cannot execute tool: {tool_name}"


def call_llm(messages: list[dict], config: dict[str, str], tools: list[dict] = None) -> dict:
    """
    Call the LLM API and return the response.

    Args:
        messages: List of message dicts (role, content)
        config: LLM configuration
        tools: Optional list of tool definitions

    Returns:
        LLM response data
    """
    api_base = config["LLM_API_BASE"]
    api_key = config["LLM_API_KEY"]
    model = config["LLM_MODEL"]

    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    # Add tools if provided
    if tools:
        payload["tools"] = tools

    print(f"Calling LLM: {model}", file=sys.stderr)

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if "choices" not in data or len(data["choices"]) == 0:
                print("Error: No choices in LLM response", file=sys.stderr)
                return None

            return data

    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
        return None
    except httpx.RequestError as e:
        print(f"Request error: {e}", file=sys.stderr)
        return None


def extract_source_from_tool_calls(tool_calls: list[dict]) -> str:
    """
    Extract source reference from tool calls.

    Args:
        tool_calls: List of tool call dicts

    Returns:
        Source string (file path with optional section anchor)
    """
    for call in tool_calls:
        if call.get("tool") == "read_file":
            path = call.get("args", {}).get("path", "")
            if path.endswith(".md"):
                # Try to extract section from the answer context
                return f"{path}"
    return ""


def run_agentic_loop(question: str, config: dict[str, str]) -> dict:
    """
    Run the agentic loop to answer a question using tools.

    Args:
        question: User's question
        config: LLM configuration

    Returns:
        Result dict with answer, source, and tool_calls
    """
    # System prompt for the documentation agent
    system_prompt = """You are a documentation assistant for a software engineering toolkit.
You have access to tools that let you read files and list directories in the project.

When answering questions:
1. Use list_files to discover what files exist in relevant directories (e.g., 'wiki', 'docs')
2. Use read_file to read the contents of specific files
3. Find the most relevant information to answer the question
4. Include a source reference in your answer (file path, and section if applicable)
5. Be concise and accurate

Available tools:
- read_file: Read contents of a file (requires 'path' argument)
- list_files: List files in a directory (requires 'path' argument)

Always use tools to find information before answering. Do not make up file contents."""

    # Initialize messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    # Get tool definitions
    tools = get_tool_definitions()

    # Track all tool calls
    all_tool_calls = []

    # Agentic loop
    for iteration in range(MAX_TOOL_CALLS):
        print(f"\n[Iteration {iteration + 1}/{MAX_TOOL_CALLS}]", file=sys.stderr)

        # Call LLM
        response = call_llm(messages, config, tools)

        if response is None:
            print("Error: LLM call failed", file=sys.stderr)
            break

        choice = response["choices"][0]
        message = choice["message"]

        # Check for tool calls
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            # No tool calls - LLM provided final answer
            print(f"\n[Final answer received]", file=sys.stderr)
            answer = message.get("content", "")
            break

        # Execute tool calls
        for tool_call in tool_calls:
            # Parse tool call
            if isinstance(tool_call, dict):
                # OpenRouter format
                func_name = tool_call.get("function", {}).get("name", "")
                func_args = tool_call.get("function", {}).get("arguments", {})

                # Parse arguments if string
                if isinstance(func_args, str):
                    try:
                        func_args = json.loads(func_args)
                    except json.JSONDecodeError:
                        func_args = {"path": func_args}
            else:
                continue

            print(f"\n[Tool call: {func_name}]", file=sys.stderr)
            print(f"  Args: {func_args}", file=sys.stderr)

            # Execute tool
            result = execute_tool(func_name, func_args)
            print(f"  Result: {result[:200]}..." if len(result) > 200 else f"  Result: {result}", file=sys.stderr)

            # Record tool call
            tool_call_record = {
                "tool": func_name,
                "args": func_args,
                "result": result
            }
            all_tool_calls.append(tool_call_record)

            # Add tool result to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "1"),
                "content": result
            })

    else:
        # Max iterations reached
        print(f"\n[Max tool calls ({MAX_TOOL_CALLS}) reached]", file=sys.stderr)
        answer = "I reached the maximum number of tool calls. Here's what I found: " + str(all_tool_calls)

    # Extract source from tool calls
    source = extract_source_from_tool_calls(all_tool_calls)

    return {
        "answer": answer,
        "source": source,
        "tool_calls": all_tool_calls
    }


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"Your question here\"", file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]

    print(f"Question: {question}", file=sys.stderr)

    config = load_config()
    result = run_agentic_loop(question, config)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
