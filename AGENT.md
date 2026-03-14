# Agent Architecture

## Overview

This agent is a CLI tool that answers questions using a Large Language Model (LLM) with tool calling capabilities. It can navigate the project repository using `read_file` and `list_files` tools, and query the deployed backend API using `query_api`. This makes it a **system agent** that can answer both documentation questions and real-time system/data queries.

## LLM Provider

**Provider:** OpenRouter  
**Model:** `nvidia/nemotron-3-super-120b-a12b:free`  
**API Base:** `https://openrouter.ai/api/v1`

## Configuration

The agent reads configuration from two environment files:

### `.env.agent.secret` (LLM Configuration)

| Variable | Description |
|----------|-------------|
| `LLM_API_KEY` | API key for OpenRouter authentication |
| `LLM_API_BASE` | Base URL of the LLM API endpoint |
| `LLM_MODEL` | Model name to use for completions |

### `.env.docker.secret` (Backend Configuration)

| Variable | Description |
|----------|-------------|
| `LMS_API_KEY` | Backend API key for `query_api` authentication |
| `AGENT_API_BASE_URL` | Optional: Base URL for backend API (default: `http://localhost:42002`) |

### Environment Variables (Runtime)

The agent also reads these from the environment (for autochecker compatibility):

| Variable | Purpose | Default |
|----------|---------|---------|
| `AGENT_API_BASE_URL` | Backend API base URL | Constructed from `.env.docker.secret` |

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐
│   User      │────▶│ agent.py │────▶│   LLM API   │
│  Question   │     │   CLI    │     │             │
└─────────────┘     └──────────┘     └─────────────┘
                          │                  │
                          │◀─────┐           │
                          │      │           │
                          ▼      │           │
                   ┌─────────────┴───────────┘
                   │
              ┌────┴────┐
              │  Tool   │
              │ Calls?  │
              └────┬────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
         ▼         ▼         ▼
   ┌──────────┐ ┌──────┐ ┌──────────┐
   │read_file │ │list_ │ │query_api │
   │          │ │files │ │(backend) │
   └────┬─────┘ └──┬───┘ └────┬─────┘
        │          │          │
        └──────────┴──────────┘
                   │
                   ▼
           ┌──────────────┐
           │ JSON Output  │
           │ {"answer":   │
           │  "...",      │
           │  "source":   │
           │  "...",      │
           │  "tool_      │
           │  calls": []} │
           └──────────────┘
```

## Tools

### 1. `read_file`

**Purpose:** Read the contents of a file from the project repository.

**Parameters:**
- `path` (string, required) — Relative path from project root (e.g., `wiki/git-workflow.md`)

**Returns:** File contents as string, or error message if file doesn't exist.

**Security:**
- Blocks paths containing `..` (directory traversal prevention)
- Validates that resolved path is within project root

### 2. `list_files`

**Purpose:** List files and directories at a given path.

**Parameters:**
- `path` (string, required) — Relative directory path from project root (e.g., `wiki`, `plans`)

**Returns:** Newline-separated listing of entries (directories first, then files).

**Security:**
- Blocks paths containing `..`
- Validates that resolved path is within project root

### 3. `query_api` (NEW in Task 3)

**Purpose:** Query the deployed backend API to get data or system information.

**Parameters:**
- `method` (string, required) — HTTP method (GET, POST, PUT, DELETE)
- `path` (string, required) — API endpoint path (e.g., `/items/`, `/analytics/completion-rate`)
- `body` (string, optional) — JSON request body for POST/PUT requests

**Returns:** JSON string with `status_code` and `body`, or error message.

**Authentication:** Uses `LMS_API_KEY` from `.env.docker.secret` via `Authorization: Bearer <token>` header.

**Example Usage:**
```bash
# Get all items
uv run agent.py "How many items are in the database?"
# → query_api with GET /items/

# Get analytics
uv run agent.py "What is the completion rate for lab-04?"
# → query_api with GET /analytics/completion-rate?lab=lab-04
```

## Agentic Loop

The agent uses an iterative loop to answer questions:

1. **Send question to LLM** — Include system prompt and tool definitions
2. **Parse response:**
   - **If tool_calls present:**
     - Execute each tool
     - Append results as `tool` role messages
     - Go to step 1 (max 10 iterations)
   - **If text message (no tool calls):**
     - Extract answer and source
     - Output JSON and exit
3. **Max iterations reached** — Use whatever answer we have

### Message Format

Messages follow the OpenAI chat format:

```json
[
  {"role": "system", "content": "You are a documentation and system assistant..."},
  {"role": "user", "content": "How many items are in the database?"},
  {"role": "assistant", "content": null, "tool_calls": [...]},
  {"role": "tool", "tool_call_id": "1", "content": "{\"status_code\": 200, ...}"}
]
```

## System Prompt Strategy

The system prompt instructs the LLM to:

1. **For wiki/documentation questions:** Use `list_files` → `read_file`
2. **For source code questions:** Use `read_file` on relevant source files
3. **For data/system questions:** Use `query_api` to query the backend
4. Include source references when applicable
5. Be concise and accurate

### Tool Selection Guide

| Question Type | Tool to Use |
|--------------|-------------|
| "What files are in..." | `list_files` |
| "Show me the contents of..." | `read_file` |
| "How many items..." | `query_api` with `GET /items/` |
| "What framework..." | `read_file` (pyproject.toml or source code) |
| "Analytics..." | `query_api` with appropriate endpoint |
| "Bug diagnosis..." | `query_api` + `read_file` |

## Output Format

The agent outputs valid JSON with three fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | string | Yes | The LLM's response to the question |
| `source` | string | Optional | Wiki section reference or API endpoint |
| `tool_calls` | array | Yes | All tool calls made during the agentic loop |

### Tool Call Format

Each entry in `tool_calls` contains:

```json
{
  "tool": "query_api",
  "args": {"method": "GET", "path": "/items/"},
  "result": "{\"status_code\": 200, \"body\": \"[...]\"}"
}
```

## Usage

```bash
# Wiki question
uv run agent.py "How do you resolve a merge conflict?"

# System question
uv run agent.py "What Python web framework does the backend use?"

# Data question
uv run agent.py "How many items are in the database?"

# Example output
{
  "answer": "There are 120 items in the database.",
  "source": "GET /items/",
  "tool_calls": [
    {"tool": "query_api", "args": {"method": "GET", "path": "/items/"}, "result": "..."}
  ]
}
```

## Dependencies

- `httpx` — HTTP client for API calls
- Python 3.14+

## Testing

Run the regression tests:

```bash
python tests/run_tests.py
python tests/test_agent_task2.py
python tests/test_agent_task3.py
```

### Test Cases

**Task 2 (Documentation Agent):**
1. "What files are in the plans directory?" — Expects `list_files`
2. "List the files in the wiki directory" — Expects `list_files`

**Task 3 (System Agent):**
1. "What framework does the backend use?" — Expects `read_file`
2. "How many items are in the database?" — Expects `query_api`

## Security

### Path Validation

`read_file` and `list_files` validate paths to prevent directory traversal:

1. Check for `..` in path
2. Resolve to absolute path
3. Verify path is within project root

### Authentication

- `LMS_API_KEY` is read from `.env.docker.secret` (gitignored)
- API key is never logged or output
- All API requests use `Authorization: Bearer <token>`

### No Secret Exposure

- `.env.agent.secret` and `.env.docker.secret` are gitignored
- API keys are never logged or output
- Tool results are sanitized

## Lessons Learned

### Challenge 1: Tool Selection

Initially, the LLM would call `read_file` for data questions like "How many items...". This was fixed by:
- Adding explicit tool selection guide in the system prompt
- Providing examples of when to use each tool
- Making `query_api` description more specific about data queries

### Challenge 2: API Authentication

The `query_api` tool needed to authenticate with the backend. Solution:
- Read `LMS_API_KEY` from `.env.docker.secret`
- Pass `Authorization: Bearer <token>` header in all requests
- Handle 401 errors gracefully

### Challenge 3: Environment Variables

The autochecker runs with different credentials. Solution:
- Read all config from environment variables
- Support `AGENT_API_BASE_URL` env var (overrides file config)
- Default to `http://localhost:42002` if not specified

### Challenge 4: Error Handling

The LLM sometimes returns `content: null` for tool calls. Solution:
- Use `(msg.get("content") or "")` instead of `msg.get("content", "")`
- Handle missing or malformed tool call responses

## Future Extensions

- **Memory:** Add conversation history for multi-turn dialogues
- **Streaming:** Stream LLM responses for better UX
- **Caching:** Cache API responses for repeated questions
- **More tools:** Add `search_code`, `run_tests`, `deploy` tools

## Final Eval Score

**Local tests:** 5/5 passed (100%)
**Hidden tests:** Pending autochecker evaluation
