# Agent Architecture

## Overview

This agent is a CLI tool that answers questions using a Large Language Model (LLM) with tool calling capabilities. It can navigate the project repository using `read_file` and `list_files` tools to find accurate information with source references.

## LLM Provider

**Provider:** OpenRouter  
**Model:** `nvidia/nemotron-3-super-120b-a12b:free`  
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
         ┌─────────┴─────────┐
         │                   │
        Yes                 No
         │                   │
         ▼                   ▼
   ┌──────────┐        ┌──────────┐
   │ Execute  │        │  Final   │
   │  Tools   │        │  Answer  │
   └────┬─────┘        └────┬─────┘
        │                   │
        │◀──────────────────┘
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
  {"role": "system", "content": "You are a documentation assistant..."},
  {"role": "user", "content": "How do you resolve a merge conflict?"},
  {"role": "assistant", "content": null, "tool_calls": [...]},
  {"role": "tool", "tool_call_id": "1", "content": "File contents..."}
]
```

## System Prompt Strategy

The system prompt instructs the LLM to:

1. Use `list_files` to discover wiki files
2. Use `read_file` to find specific information
3. Include source references (file path + section anchor)
4. Be concise and accurate
5. Use tools before answering (don't make up file contents)

## Output Format

The agent outputs valid JSON with three fields:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | The LLM's response to the question |
| `source` | string | Wiki section reference (e.g., `wiki/git-workflow.md`) |
| `tool_calls` | array | All tool calls made during the agentic loop |

### Tool Call Format

Each entry in `tool_calls` contains:

```json
{
  "tool": "read_file",
  "args": {"path": "wiki/git-workflow.md"},
  "result": "File contents..."
}
```

## Usage

```bash
# Run with a question
uv run agent.py "How do you resolve a merge conflict?"

# Example output
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "git-workflow.md\n..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
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
```

### Test Cases

1. **"How do you resolve a merge conflict?"** — Expects `read_file` in tool_calls
2. **"What files are in the wiki?"** — Expects `list_files` in tool_calls

## Security

### Path Validation

Both tools validate paths to prevent directory traversal:

1. Check for `..` in path
2. Resolve to absolute path
3. Verify path is within project root

### No Secret Exposure

- `.env.agent.secret` is gitignored
- API keys are never logged or output
- Tool results are sanitized

## Future Extensions

- **Task 3:** Add domain-specific tools (query database, call LMS API)
- **Memory:** Add conversation history for multi-turn dialogues
- **Streaming:** Stream LLM responses for better UX
- **Caching:** Cache file reads for repeated questions
