# Task 3: The System Agent - Implementation Plan

## Overview
This task adds a `query_api` tool to the agent from Task 2, enabling it to query the deployed backend API for system facts and data-dependent queries.

## Implementation Plan

### 1. query_api Tool Schema
The tool is already defined in `agent.py` with:
- **Parameters**: `method` (GET/POST/PUT/DELETE), `path` (endpoint), `body` (optional JSON)
- **Returns**: JSON string with `status_code` and `body`
- **Authentication**: Uses `LMS_API_KEY` from `.env.docker.secret`

### 2. Authentication Handling
- Read `LMS_API_KEY` from environment variable or `.env.docker.secret`
- Include `Authorization: Bearer {LMS_API_KEY}` header in all API requests
- `AGENT_API_BASE_URL` from environment (default: `http://localhost:42002`)

### 3. System Prompt Updates
The system prompt needs to be more explicit about:
- **When to use query_api**: For runtime data (item counts, analytics, status codes)
- **When to use read_file**: For static facts (framework, code structure, configuration)
- **When to use list_files**: For discovering wiki/documentation files

### 4. Key Issues to Fix

#### Issue 1: Agent doesn't authenticate API requests properly
**Problem**: The agent may not be sending the API key correctly.
**Fix**: Ensure `load_lms_config()` reads from environment first, then file.

#### Issue 2: Agent doesn't handle API errors correctly
**Problem**: When API returns 401/403, agent thinks 200 is normal.
**Fix**: Improve error handling and teach agent to interpret status codes.

#### Issue 3: System prompt too vague
**Problem**: Agent doesn't know when to use which tool.
**Fix**: Add explicit examples and decision criteria.

#### Issue 4: Tool call argument parsing
**Problem**: Arguments may not be parsed correctly from LLM response.
**Fix**: Ensure robust JSON parsing with fallbacks.

### 5. Environment Variable Handling
All configuration must come from environment variables:
- `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` → LLM config
- `LMS_API_KEY` → Backend API authentication
- `AGENT_API_BASE_URL` → Backend URL (optional, defaults to localhost)

The autochecker injects its own values, so no hardcoded values.

## Benchmark Results (Initial Run)

```
Score: 0/5 passed (0%)

Failed questions:
1. [Wiki] Branch protection steps - agent didn't find wiki files
2. [Framework] Python web framework - agent guessed instead of reading code
3. [Data] Item count - query_api didn't work or returned wrong data
4. [Bug] Analytics completion-rate - agent didn't diagnose the bug
5. [Architecture] Request lifecycle - agent didn't trace through files
```

## Iteration Strategy

1. **Fix query_api authentication** - Ensure LMS_API_KEY is used correctly ✓
2. **Improve system prompt** - Add explicit tool selection rules ✓
3. **Add error handling** - Teach agent to interpret HTTP status codes ✓
4. **Test each question class** - Run eval, fix one class at a time
5. **Add regression tests** - Ensure fixes don't break existing functionality ✓

## Implementation Changes Made

### 1. Environment Variable Handling
- `load_config()` now checks `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL` from environment first
- `load_lms_config()` now checks `LMS_API_KEY` from environment first
- `get_api_base_url()` now checks `AGENT_API_BASE_URL` from environment first
- All functions fall back to `.env` files for local development

### 2. System Prompt Rewrite
- Added explicit "Tool Selection Rules" section with when-to-use-what
- Added "Important Guidelines" for HTTP status codes, authentication, wiki questions
- Added concrete examples for each question type
- Added decision criteria: list_files vs read_file vs query_api

### 3. Test Coverage
- Added `test_agent_uses_list_files_for_api_routers` - Verifies file discovery
- Added `test_agent_reads_dockerfile_for_multi_stage` - Verifies Dockerfile reading
- Total: 5 regression tests for Task 3

## Lessons Learned

### Tool Selection Requires Explicit Instructions
The LLM needs very specific guidance about which tool to use. Vague descriptions like "use for data questions" are insufficient. We added:
- Decision trees organized by question type
- Concrete examples for each tool
- Explicit workflows for multi-step tasks (e.g., wiki navigation)

### Environment Variable Injection is Critical
The autochecker runs with different credentials. Reading from environment variables first ensures compatibility with both local development and automated evaluation.

### HTTP Status Code Questions Require Live Testing
The agent was reading documentation instead of testing endpoints. We added explicit instruction: "For HTTP status code questions, you MUST use query_api to make the actual request. Documentation may be outdated."

### Multi-Step Tasks Need Step-by-Step Instructions
For "according to the wiki" questions, the agent needs explicit workflow: list_files → read_file → find section. Single-sentence instructions are not enough.
