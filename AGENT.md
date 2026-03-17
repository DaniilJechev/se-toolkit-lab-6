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
4. **For HTTP status code questions:** Use `query_api` to TEST the actual endpoint (docs may be outdated)
5. Include source references when applicable
6. Be concise and accurate

### Tool Selection Guide

| Question Type | Tool to Use | Example |
|--------------|-------------|---------|
| "What files are in..." | `list_files` | "What files are in the wiki directory?" |
| "Show me the contents of..." | `read_file` | "Show me the contents of main.py" |
| "How many items..." | `query_api` | "How many items are in the database?" |
| "What framework..." | `read_file` | "What Python web framework does the backend use?" |
| "List all routers..." | `list_files` + `read_file` | "List all API router modules" |
| "What status code..." | `query_api` | "What status code does /items/ return?" |
| "According to the wiki..." | `list_files` + `read_file` | "According to the wiki, how to protect a branch?" |
| "Read the Dockerfile..." | `read_file` | "Read the Dockerfile. What technique is used?" |
| "Bug diagnosis..." | `query_api` + `read_file` | "Query /analytics/completion-rate and find the bug" |
| "Compare X and Y..." | Multiple `read_file` calls | "Compare ETL error handling vs API error handling" |

### Decision Criteria

The system prompt includes explicit decision criteria:

**Use `list_files` when:**
- Question asks "what files are in...", "list all...", "find files about..."
- You need to discover wiki/documentation files

**Use `read_file` when:**
- Question asks about static facts: framework, architecture, configuration
- Question asks to read source code, documentation, or configuration files
- Question contains: "what framework", "what does", "explain", "read the", "according to"

**Use `query_api` when:**
- Question asks about runtime data: counts, current state, dynamic information
- Question asks "how many", "what is the current", "query the API"
- Question asks about HTTP status codes (you must TEST the API, not read docs)

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

### Challenge 1: Tool Selection Ambiguity

**Problem:** Initially, the LLM would call `read_file` for data questions like "How many items..." or guess the framework instead of reading the code.

**Solution:** 
- Rewrote the system prompt with explicit tool selection rules organized by question type
- Added a "Decision Criteria" section with clear when-to-use-what guidelines
- Provided concrete examples for each tool
- Emphasized that HTTP status codes require `query_api` to TEST the actual endpoint (documentation may be outdated)

**Key Insight:** The LLM needs very explicit instructions about tool selection. Vague descriptions like "use for data questions" are not enough — specific examples and decision trees work much better.

### Challenge 2: API Authentication

**Problem:** The `query_api` tool needed to authenticate with the backend using `LMS_API_KEY`, but the autochecker injects different credentials at runtime.

**Solution:**
- Modified `load_lms_config()` to check environment variables first, then fall back to `.env.docker.secret`
- Modified `get_api_base_url()` to check `AGENT_API_BASE_URL` environment variable first
- Modified `load_config()` to check LLM environment variables first
- This ensures compatibility with both local development and autochecker evaluation

**Key Insight:** Always read configuration from environment variables first for testability and CI/CD compatibility.

### Challenge 3: HTTP Status Code Questions

**Problem:** The agent was reading documentation to answer "What status code does /items/ return?" instead of actually testing the endpoint.

**Solution:**
- Added explicit instruction in system prompt: "For HTTP status code questions, you MUST use query_api to make the actual request. Documentation may be outdated."
- Added examples showing that status code questions require `query_api`

**Key Insight:** Distinguish between static knowledge (framework, architecture) and runtime knowledge (status codes, data counts). The latter requires live API calls.

### Challenge 4: Wiki Navigation

**Problem:** For "According to the wiki..." questions, the agent needed to first discover which wiki file contains the answer.

**Solution:**
- Added explicit workflow: "For 'according to the wiki' questions: First use list_files wiki/ to find relevant files, then read_file the specific .md file, look for the exact section mentioned."
- The agent now systematically searches for relevant wiki files before reading

**Key Insight:** Multi-step tasks need explicit step-by-step instructions in the system prompt.

### Challenge 5: Environment Variable Handling

**Problem:** The autochecker runs with different LLM credentials and backend URL. Hardcoded values would fail.

**Solution:**
- All configuration functions (`load_config`, `load_lms_config`, `get_api_base_url`) now check environment variables first
- Fall back to `.env` files only for local development
- Added comments explaining the autochecker injection mechanism

**Key Insight:** Design for testability from the start. Environment variable injection is a standard pattern for CI/CD.

### Challenge 6: Error Handling in Agentic Loop

**Problem:** The LLM sometimes returns `content: null` when making tool calls, causing `AttributeError` with `.get()`.

**Solution:**
- Use `(msg.get("content") or "")` instead of `msg.get("content", "")` — the field is present but null, not missing
- Handle malformed tool call responses gracefully
- Provide fallback answers when LLM calls fail

**Key Insight:** Always assume LLM responses can be malformed. Defensive programming is essential.

### Challenge 7: Bug Diagnosis Questions

**Problem:** For "diagnose the bug in /analytics/completion-rate" questions, the agent needs to chain multiple tools.

**Solution:**
- Added explicit workflow in system prompt: "First query_api to see the error response, then read_file the relevant source code, compare expected vs actual behavior"
- The agent now learns to correlate API error messages with source code patterns

**Key Insight:** Complex reasoning tasks require explicit multi-step workflows in the system prompt.

## Final Eval Score

**Local tests:** 5/5 passed (100%)
**Hidden tests:** Pending autochecker evaluation

**Test Coverage:**
- `test_agent_uses_query_api_for_data` — Verifies `query_api` for count questions
- `test_agent_uses_read_file_for_framework` — Verifies `read_file` for framework questions
- `test_agent_query_api_authentication` — Verifies API authentication works
- `test_agent_uses_list_files_for_api_routers` — Verifies file discovery for router listing
- `test_agent_reads_dockerfile_for_multi_stage` — Verifies Dockerfile reading for architecture questions

## Future Extensions

- **Memory:** Add conversation history for multi-turn dialogues
- **Streaming:** Stream LLM responses for better UX
- **Caching:** Cache API responses for repeated questions
- **More tools:** Add `search_code`, `run_tests`, `deploy` tools
