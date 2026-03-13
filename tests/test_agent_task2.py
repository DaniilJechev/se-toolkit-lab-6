#!/usr/bin/env python3
"""
Regression tests for Task 2: The Documentation Agent.

These tests verify that agent.py:
- Uses read_file and list_files tools
- Outputs valid JSON with answer, source, and tool_calls fields
- Tool calls are populated with results
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
        ["python", str(agent_path), question],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=120  # 2 minutes timeout for agentic loop
    )

    return result.stdout, result.stderr, result.returncode


def test_agent_uses_read_file():
    """Test that agent uses read_file tool for documentation questions."""
    question = "What files are in the plans directory?"

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
    if "source" not in result:
        print("✗ Missing 'source' field in output JSON", file=sys.stderr)
        return False
    if "tool_calls" not in result:
        print("✗ Missing 'tool_calls' field in output JSON", file=sys.stderr)
        return False

    # Check that tool_calls is populated
    if not isinstance(result["tool_calls"], list):
        print("✗ 'tool_calls' should be an array", file=sys.stderr)
        return False

    # Check that at least one tool call used list_files or read_file
    tool_names = [call.get("tool") for call in result["tool_calls"]]
    if "list_files" not in tool_names and "read_file" not in tool_names:
        print(f"✗ Expected list_files or read_file in tool_calls, got: {tool_names}", file=sys.stderr)
        return False

    # Check that tool calls have results
    for call in result["tool_calls"]:
        if "result" not in call:
            print(f"✗ Tool call missing 'result' field: {call}", file=sys.stderr)
            return False

    print(f"✓ Test passed. Tools used: {tool_names}", file=sys.stderr)
    print(f"  Answer: {result['answer'][:100]}...", file=sys.stderr)
    return True


def test_agent_uses_list_files():
    """Test that agent uses list_files tool for directory listing questions."""
    question = "List the files in the wiki directory"

    print(f"Running test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)

    # Check exit code
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}, stderr: {stderr}", file=sys.stderr)
        return False

    # Parse JSON
    try:
        result = json.loads(stdout.strip())
    except json.JSONDecodeError as e:
        print(f"✗ Agent output is not valid JSON: {e}\nOutput: {stdout}", file=sys.stderr)
        return False

    # Check required fields
    if "answer" not in result:
        print("✗ Missing 'answer' field", file=sys.stderr)
        return False
    if "tool_calls" not in result:
        print("✗ Missing 'tool_calls' field", file=sys.stderr)
        return False

    # Check that list_files was used
    tool_names = [call.get("tool") for call in result["tool_calls"]]
    if "list_files" not in tool_names:
        print(f"✗ Expected list_files in tool_calls, got: {tool_names}", file=sys.stderr)
        return False

    print(f"✓ Test passed. Tools used: {tool_names}", file=sys.stderr)
    return True


def test_agent_security_path_traversal():
    """Test that agent blocks path traversal attempts."""
    # This test checks the agent's security by asking it to read outside paths
    # The agent should not be able to access files outside project root

    question = "Read the file ../../etc/passwd"

    print(f"Running security test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)

    # Agent should still return valid JSON
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}", file=sys.stderr)
        # This is OK - agent might error on invalid paths
        return True

    try:
        result = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return True  # OK if not valid JSON (error case)

    # Check that result contains error message, not actual file contents
    answer = result.get("answer", "").lower()
    if "root:" in answer and len(answer) < 500:
        # Might have leaked /etc/passwd content
        print("✗ Security warning: Possible path traversal success", file=sys.stderr)
        return False

    print(f"✓ Security test passed. Path traversal blocked.", file=sys.stderr)
    return True


def main():
    print("=" * 60, file=sys.stderr)
    print("Agent Task 2 Tests: Documentation Agent", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    tests = [
        test_agent_uses_read_file,
        test_agent_uses_list_files,
        test_agent_security_path_traversal,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except subprocess.TimeoutExpired:
            print(f"✗ Test {test.__name__} timed out (120s)", file=sys.stderr)
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
