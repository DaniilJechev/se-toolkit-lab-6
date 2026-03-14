# Task 3 Plan: The System Agent

## Overview

Add a `query_api` tool to the documentation agent so it can query the deployed backend API. This enables the agent to answer static system facts (framework, ports, status codes) and data-dependent queries (item count, scores).

## LLM Provider

**Provider:** OpenRouter  
**Model:** `nvidia/nemotron-3-super-120b-a12b:free`  
**API Base:** `https://openrouter.ai/api/v1`

## New Tool: query_api

**Purpose:** Send HTTP requests to the deployed backend API.

**Parameters:**
- `method` (string, required) — HTTP method (GET, POST, PUT, DELETE)
- `path` (string, required) — API endpoint path (e.g., `/items/`, `/analytics/completion-rate`)
- `body` (string, optional) — JSON request body for POST/PUT requests

**Returns:** JSON string with `status_code` and `body`.

**Authentication:** Uses `LMS_API_KEY` from `.env.docker.secret` via `Authorization: Bearer <token>` header.

## Environment Variables

The agent must read these from environment (not hardcoded):

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key for query_api auth | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Base URL for query_api | Optional, defaults to `http://localhost:42002` |

## Implementation Steps

1. **Add `query_api` function** to `agent.py`:
   - Accept method, path, body parameters
   - Read `LMS_API_KEY` from `.env.docker.secret`
   - Read `AGENT_API_BASE_URL` from environment (default: `http://localhost:42002`)
   - Send HTTP request with `Authorization: Bearer <LMS_API_KEY>`
   - Return JSON response with status_code and body

2. **Add tool schema** for function calling:
   ```json
   {
     "type": "function",
     "function": {
       "name": "query_api",
       "description": "Query the deployed backend API",
       "parameters": {
         "type": "object",
         "properties": {
           "method": {"type": "string", "description": "HTTP method (GET, POST, etc.)"},
           "path": {"type": "string", "description": "API endpoint path (e.g., /items/)"},
           "body": {"type": "string", "description": "JSON request body (optional)"}
         },
         "required": ["method", "path"]
       }
     }
   }
   ```

3. **Update system prompt** to guide LLM:
   - Use `list_files` to discover wiki files
   - Use `read_file` to read documentation or source code
   - Use `query_api` to query the backend for data or system info
   - Choose the right tool based on question type

4. **Update output format**:
   - `source` is now optional (system questions may not have wiki source)

5. **Run the benchmark**:
   ```bash
   uv run run_eval.py
   ```

6. **Iterate** based on failures:
   - Fix tool descriptions
   - Fix bugs in tool implementation
   - Adjust system prompt

## Tool Selection Strategy

| Question Type | Tool to Use |
|--------------|-------------|
| Wiki documentation | `list_files` → `read_file` |
| System facts (framework, ports) | `read_file` (source code) or `query_api` |
| Data queries (item count, scores) | `query_api` |
| Bug diagnosis | `read_file` (source code) + `query_api` (error info) |

## Testing Strategy

**Test 1:** "What framework does the backend use?"
- Expected: `read_file` in tool_calls (reading pyproject.toml or backend code)

**Test 2:** "How many items are in the database?"
- Expected: `query_api` in tool_calls with `GET /items/`

## Benchmark Questions

The `run_eval.py` script tests 10 questions:
1. Wiki lookup (branch protection steps)
2. System fact (web framework)
3. Data query (item count)
4. Analytics endpoint (completion rate for lab-99)
5. Bug diagnosis
6. Reasoning questions
7-10. Additional challenges

## Files to Modify

- `agent.py` — add `query_api` tool and update system prompt
- `AGENT.md` — update documentation
- `tests/test_agent_task3.py` — new tests

## Success Criteria

- All 10 `run_eval.py` questions pass
- Agent correctly chooses between wiki tools and `query_api`
- Authentication works with `LMS_API_KEY`
- No hardcoded values (all config from environment)
