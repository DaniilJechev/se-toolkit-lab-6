# Task 2 Plan: The Documentation Agent

## Overview

Build an agentic loop that allows the LLM to use tools (`read_file`, `list_files`) to navigate the project wiki and answer questions with source references.

## LLM Provider

**Provider:** OpenRouter  
**Model:** `nvidia/nemotron-3-super-120b-a12b:free`  
**API Base:** `https://openrouter.ai/api/v1`

## Tool Definitions

### 1. `read_file`

**Purpose:** Read contents of a file from the project repository.

**Parameters:**
- `path` (string, required) — relative path from project root

**Security:**
- Block paths containing `..` (directory traversal)
- Resolve to absolute path and verify it's within project root

**Returns:** File contents as string, or error message if file doesn't exist.

### 2. `list_files`

**Purpose:** List files and directories at a given path.

**Parameters:**
- `path` (string, required) — relative directory path from project root

**Security:**
- Block paths containing `..`
- Resolve and verify directory is within project root

**Returns:** Newline-separated listing of entries.

## Function Calling Schema

Define tools in OpenAI-compatible format:

```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read the contents of a file",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {"type": "string", "description": "Relative path from project root"}
      },
      "required": ["path"]
    }
  }
}
```

Similar schema for `list_files`.

## Agentic Loop

```
1. Send user question + tool definitions to LLM
2. Parse LLM response:
   - If tool_calls present:
     a. Execute each tool call
     b. Append results as tool role messages
     c. Go to step 1 (max 10 iterations)
   - If text message (no tool calls):
     a. Extract answer and source
     b. Output JSON and exit
3. If max iterations reached → use whatever answer we have
```

## System Prompt Strategy

Tell the LLM:
1. Use `list_files` to discover wiki files
2. Use `read_file` to find specific information
3. Always include source reference (file path + section anchor)
4. Return answer in the format expected by the CLI

## Output Format

```json
{
  "answer": "...",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}
```

## Implementation Steps

1. **Add tool functions** to `agent.py`:
   - `read_file(path: str) -> str`
   - `list_files(path: str) -> str`

2. **Add path security**:
   - Validate paths don't escape project root

3. **Define tool schemas** for LLM API request

4. **Implement agentic loop**:
   - Parse tool calls from LLM response
   - Execute tools
   - Feed results back to LLM

5. **Update output format**:
   - Add `source` field
   - Populate `tool_calls` with results

6. **Update AGENT.md** with new architecture

7. **Add tests**:
   - Test question that requires `read_file`
   - Test question that requires `list_files`

## Files to Modify

- `agent.py` — add tools and agentic loop
- `AGENT.md` — update documentation
- `tests/test_agent_task2.py` — new tests (or extend existing)

## Testing Strategy

**Test 1:** "How do you resolve a merge conflict?"
- Expected: `read_file` in tool_calls
- Expected: `wiki/git-workflow.md` in source

**Test 2:** "What files are in the wiki?"
- Expected: `list_files` in tool_calls
- Expected: non-empty tool_calls array
