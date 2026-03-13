"""
Regression tests for Task 1: Call an LLM from Code.

These tests verify that agent.py:
- Accepts a question as command-line argument
- Outputs valid JSON to stdout
- Contains required fields: 'answer' and 'tool_calls'
"""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str) -> tuple[str, str, int]:
    """Run agent.py with a question and return (stdout, stderr, returncode)."""
    project_root = Path(__file__).parent.parent
    agent_path = project_root / "agent.py"
    
    result = subprocess.run(
        ["uv", "run", "agent.py", question],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    
    return result.stdout, result.stderr, result.returncode


def test_agent_outputs_valid_json():
    """Test that agent.py outputs valid JSON with required fields."""
    question = "What does REST stand for?"
    
    stdout, stderr, returncode = run_agent(question)
    
    # Check exit code
    assert returncode == 0, f"Agent exited with code {returncode}, stderr: {stderr}"
    
    # Check that stdout is not empty
    assert stdout.strip(), "Agent produced no output to stdout"
    
    # Parse JSON
    try:
        result = json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        raise AssertionError(f"Agent output is not valid JSON: {e}\nOutput: {stdout}")
    
    # Check required fields
    assert "answer" in result, "Missing 'answer' field in output JSON"
    assert "tool_calls" in result, "Missing 'tool_calls' field in output JSON"
    
    # Check field types
    assert isinstance(result["answer"], str), "'answer' should be a string"
    assert isinstance(result["tool_calls"], list), "'tool_calls' should be an array"
    
    # Check that answer is not empty
    assert len(result["answer"].strip()) > 0, "'answer' field is empty"
    
    print(f"✓ Test passed. Answer: {result['answer'][:100]}...", file=sys.stderr)


def test_agent_tool_calls_is_empty():
    """Test that tool_calls is an empty array for Task 1."""
    question = "What is 2 + 2?"
    
    stdout, stderr, returncode = run_agent(question)
    
    assert returncode == 0, f"Agent exited with code {returncode}"
    
    result = json.loads(stdout.strip())
    
    assert result["tool_calls"] == [], f"tool_calls should be empty, got: {result['tool_calls']}"
    
    print(f"✓ Test passed. tool_calls is empty array.", file=sys.stderr)


if __name__ == "__main__":
    import pytest
    
    pytest.main([__file__, "-v"])
