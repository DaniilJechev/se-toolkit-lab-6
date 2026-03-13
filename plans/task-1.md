# Task 1 Plan: Call an LLM from Code

## LLM Provider Choice

**Provider:** OpenRouter  
**Model:** `meta-llama/llama-3.3-70b-instruct:free`  
**Reason:** Already have API key, free tier available, OpenAI-compatible API.

## Architecture

```
User Question → agent.py → OpenRouter API → JSON Response
```

## Implementation Steps

1. **Read environment variables** from `.env.agent.secret`:
   - `LLM_API_KEY` - API key for authentication
   - `LLM_API_BASE` - Base URL (https://openrouter.ai/api/v1)
   - `LLM_MODEL` - Model name

2. **Parse command-line arguments**:
   - Accept question as first positional argument
   - Validate input (exit with error if no question provided)

3. **Call LLM API**:
   - Use `requests` or `httpx` library
   - Send POST request to `{LLM_API_BASE}/chat/completions`
   - Include Authorization header with Bearer token
   - Use OpenAI-compatible message format

4. **Format response**:
   - Extract answer from LLM response
   - Create JSON structure: `{"answer": "...", "tool_calls": []}`
   - Output valid JSON to stdout
   - Send debug/progress info to stderr

5. **Error handling**:
   - Handle network errors
   - Handle API errors (401, 429, 500)
   - Exit with code 0 on success, non-zero on failure

## Testing

- Create test in `tests/test_agent_task1.py`
- Run `agent.py` as subprocess
- Parse stdout JSON
- Verify `answer` and `tool_calls` fields exist
- Verify `tool_calls` is empty array

## Files to Create

- `agent.py` - Main CLI agent
- `AGENT.md` - Documentation
- `tests/test_agent_task1.py` - Regression test
