# Agent Architecture

## Overview

This agent is a CLI tool that answers questions using a Large Language Model (LLM). It serves as the foundation for the learning management service assistant.

## LLM Provider

**Provider:** OpenRouter  
**Model:** `meta-llama/llama-3.3-70b-instruct:free`  
**API Base:** `https://openrouter.ai/api/v1`

## Configuration

The agent reads configuration from `.env.agent.secret`:

| Variable | Description |
|----------|-------------|
| `LLM_API_KEY` | API key for OpenRouter authentication |
| `LLM_API_BASE` | Base URL of the LLM API endpoint |
| `LLM_MODEL` | Model name to use for completions |

## Architecture

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────┐
│   User      │────▶│ agent.py │────▶│ OpenRouter  │────▶│   LLM    │
│  Question   │     │   CLI    │     │    API      │     │  Model   │
└─────────────┘     └──────────┘     └─────────────┘     └──────────┘
                          │                                      │
                          │◀─────────────────────────────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ JSON Output  │
                   │ {"answer":   │
                   │  "tool_      │
                   │  calls": []} │
                   └──────────────┘
```

## Data Flow

1. **Input Parsing**: The agent accepts a question as the first command-line argument.

2. **Configuration Loading**: Reads `.env.agent.secret` to get API credentials.

3. **API Call**: Sends a POST request to the LLM's chat completions endpoint with:
   - System prompt: "You are a helpful assistant..."
   - User message: The question from the command line

4. **Response Processing**: Extracts the answer from the LLM response and formats it as JSON.

5. **Output**: Prints a single JSON line to stdout:
   ```json
   {"answer": "...", "tool_calls": []}
   ```

## Output Format

The agent outputs valid JSON with two required fields:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | The LLM's response to the question |
| `tool_calls` | array | Empty array (will be populated in Task 2) |

## Error Handling

- **Missing arguments**: Exits with usage message to stderr
- **Missing config**: Exits with error listing missing keys
- **Network errors**: Exits with error message to stderr
- **API errors**: Exits with HTTP status and response body

All debug and error output goes to **stderr**. Only the final JSON result goes to **stdout**.

## Usage

```bash
# Run with a question
uv run agent.py "What does REST stand for?"

# Example output
{"answer": "Representational State Transfer.", "tool_calls": []}
```

## Dependencies

- `httpx` - HTTP client for API calls
- Python 3.14+

## Testing

Run the regression test:

```bash
uv run pytest tests/test_agent_task1.py -v
```

## Future Extensions

- **Task 2**: Add tool support (database queries, API calls)
- **Task 3**: Add agentic loop for multi-step reasoning
- **Domain knowledge**: Add system prompt with LMS-specific information
