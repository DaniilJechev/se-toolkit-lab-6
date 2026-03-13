#!/usr/bin/env python3
"""
Simple test runner for agent tests (no pytest required).
"""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str) -> tuple[str, str, int]:
    """Run agent.py with a question and return (stdout, stderr, returncode)."""
    project_root = Path(__file__).parent.parent  # Go up from tests/ to project root
    agent_path = project_root / "agent.py"
    
    result = subprocess.run(
        ["python", str(agent_path), question],
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    
    return result.stdout, result.stderr, result.returncode


def test_agent_outputs_valid_json():
    """Test that agent.py outputs valid JSON with required fields."""
    question = "What does REST stand for?"
    
    print(f"Running test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)
    
    # Check exit code
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}, stderr: {stderr}", file=sys.stderr)
        return False
    
    # Check that stdout is not empty
    if not stdout.strip():
        print("✗ Agent produced no output to stdout", file=sys.stderr)
        return False
    
    # Parse JSON
    try:
        result = json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        print(f"✗ Agent output is not valid JSON: {e}\nOutput: {stdout}", file=sys.stderr)
        return False
    
    # Check required fields
    if "answer" not in result:
        print("✗ Missing 'answer' field in output JSON", file=sys.stderr)
        return False
    if "tool_calls" not in result:
        print("✗ Missing 'tool_calls' field in output JSON", file=sys.stderr)
        return False
    
    # Check field types
    if not isinstance(result["answer"], str):
        print("✗ 'answer' should be a string", file=sys.stderr)
        return False
    if not isinstance(result["tool_calls"], list):
        print("✗ 'tool_calls' should be an array", file=sys.stderr)
        return False
    
    # Check that answer is not empty
    if len(result["answer"].strip()) == 0:
        print("✗ 'answer' field is empty", file=sys.stderr)
        return False
    
    print(f"✓ Test passed. Answer: {result['answer'][:100]}...", file=sys.stderr)
    return True


def test_agent_tool_calls_is_empty():
    """Test that tool_calls is an empty array for Task 1."""
    question = "What is 2 + 2?"
    
    print(f"Running test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)
    
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}", file=sys.stderr)
        return False
    
    result = json.loads(stdout.strip())
    
    if result["tool_calls"] != []:
        print(f"✗ tool_calls should be empty, got: {result['tool_calls']}", file=sys.stderr)
        return False
    
    print(f"✓ Test passed. tool_calls is empty array.", file=sys.stderr)
    return True


def main():
    print("=" * 60, file=sys.stderr)
    print("Agent Task 1 Tests", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    tests = [
        test_agent_outputs_valid_json,
        test_agent_tool_calls_is_empty,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} raised exception: {e}", file=sys.stderr)
            failed += 1
    
    print("=" * 60, file=sys.stderr)
    print(f"Results: {passed} passed, {failed} failed", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
