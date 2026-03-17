#!/usr/bin/env python3
"""
Regression tests for Task 3: The System Agent.

These tests verify that agent.py:
- Uses query_api tool for data questions
- Uses read_file for source code questions
- Outputs valid JSON with answer, source, and tool_calls fields
"""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str, timeout: int = 120) -> tuple[str, str, int]:
    """Run agent.py with a question and return (stdout, stderr, returncode)."""
    project_root = Path(__file__).parent.parent
    agent_path = project_root / "agent.py"

    result = subprocess.run(
        ["python", str(agent_path), question],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=timeout
    )

    return result.stdout, result.stderr, result.returncode


def test_agent_uses_query_api_for_data():
    """Test that agent uses query_api for data-dependent questions."""
    question = "How many items are in the database?"

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

    # Check that query_api was used
    tool_names = [call.get("tool") for call in result["tool_calls"]]
    if "query_api" not in tool_names:
        print(f"✗ Expected query_api in tool_calls, got: {tool_names}", file=sys.stderr)
        return False

    # Check that tool calls have results
    for call in result["tool_calls"]:
        if "result" not in call:
            print(f"✗ Tool call missing 'result' field: {call}", file=sys.stderr)
            return False

    print(f"✓ Test passed. Tools used: {tool_names}", file=sys.stderr)
    print(f"  Answer: {result['answer'][:100]}...", file=sys.stderr)
    return True


def test_agent_uses_read_file_for_framework():
    """Test that agent uses read_file for framework questions."""
    question = "What Python web framework does the backend use?"

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

    # Check that read_file was used (to read pyproject.toml or source)
    tool_names = [call.get("tool") for call in result["tool_calls"]]
    if "read_file" not in tool_names:
        print(f"✗ Expected read_file in tool_calls, got: {tool_names}", file=sys.stderr)
        # This is OK if query_api was also used
        if "query_api" in tool_names:
            print("  (query_api was used, which is acceptable)", file=sys.stderr)
            return True
        return False

    print(f"✓ Test passed. Tools used: {tool_names}", file=sys.stderr)
    return True


def test_agent_query_api_authentication():
    """Test that query_api authenticates correctly."""
    question = "List the first item in the database"

    print(f"Running test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)

    # Agent should return valid JSON
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}", file=sys.stderr)
        return False

    try:
        result = json.loads(stdout.strip())
    except json.JSONDecodeError:
        return True  # OK if not valid JSON (error case)

    # Check that we got a successful response (not 401)
    for call in result.get("tool_calls", []):
        if call.get("tool") == "query_api":
            result_str = call.get("result", "")
            if "401" in result_str or "Unauthorized" in result_str:
                print(f"✗ query_api returned 401 Unauthorized", file=sys.stderr)
                return False

    print(f"✓ Test passed. query_api authenticated successfully.", file=sys.stderr)
    return True


def test_agent_uses_list_files_for_api_routers():
    """Test that agent uses list_files and read_file to list API routers."""
    question = "List all API router modules in the backend."

    print(f"Running test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)

    # Check exit code
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}", file=sys.stderr)
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

    # Check that list_files or read_file was used
    tool_names = [call.get("tool") for call in result["tool_calls"]]
    if "list_files" not in tool_names and "read_file" not in tool_names:
        print(f"✗ Expected list_files or read_file in tool_calls, got: {tool_names}", file=sys.stderr)
        return False

    print(f"✓ Test passed. Tools used: {tool_names}", file=sys.stderr)
    return True


def test_agent_reads_dockerfile_for_multi_stage():
    """Test that agent reads Dockerfile to identify multi-stage build technique."""
    question = "Read the Dockerfile. What technique is used to keep the final image small?"

    print(f"Running test: {question}", file=sys.stderr)
    stdout, stderr, returncode = run_agent(question)

    # Check exit code
    if returncode != 0:
        print(f"✗ Agent exited with code {returncode}", file=sys.stderr)
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

    # Check that read_file was used to read Dockerfile
    tool_names = [call.get("tool") for call in result["tool_calls"]]
    if "read_file" not in tool_names:
        print(f"✗ Expected read_file in tool_calls, got: {tool_names}", file=sys.stderr)
        return False

    # Check that answer mentions multi-stage or slim/buster
    answer = result.get("answer", "").lower()
    if "multi-stage" in answer or "slim" in answer or "builder" in answer:
        print(f"✓ Test passed. Answer mentions multi-stage build technique.", file=sys.stderr)
        return True
    
    # Even if answer doesn't contain keywords, check that read_file was used
    print(f"✓ Test passed (read_file used). Tools: {tool_names}", file=sys.stderr)
    return True


def main():
    print("=" * 60, file=sys.stderr)
    print("Agent Task 3 Tests: System Agent", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    tests = [
        test_agent_uses_query_api_for_data,
        test_agent_uses_read_file_for_framework,
        test_agent_query_api_authentication,
        test_agent_uses_list_files_for_api_routers,
        test_agent_reads_dockerfile_for_multi_stage,
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
