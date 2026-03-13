#!/usr/bin/env python3
"""
Learning Management Service Agent

A CLI tool that answers questions using an LLM.
Usage: uv run agent.py "Your question here"
"""

import json
import os
import sys
from pathlib import Path

import httpx


def load_env(env_path: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def load_config() -> dict[str, str]:
    """Load LLM configuration from .env.agent.secret."""
    project_root = Path(__file__).parent
    env_path = project_root / ".env.agent.secret"
    
    config = load_env(env_path)
    
    required_keys = ["LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL"]
    missing = [key for key in required_keys if key not in config]
    
    if missing:
        print(f"Error: Missing required config keys: {missing}", file=sys.stderr)
        print("Please create .env.agent.secret with required values.", file=sys.stderr)
        sys.exit(1)
    
    return config


def call_llm(question: str, config: dict[str, str]) -> str:
    """Call the LLM API and return the answer."""
    api_base = config["LLM_API_BASE"]
    api_key = config["LLM_API_KEY"]
    model = config["LLM_MODEL"]
    
    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions concisely and accurately."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    
    print(f"Calling LLM: {model}", file=sys.stderr)
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                print("Error: No choices in LLM response", file=sys.stderr)
                sys.exit(1)
            
            answer = data["choices"][0]["message"]["content"]
            return answer
            
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Request error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"Your question here\"", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    
    print(f"Question: {question}", file=sys.stderr)
    
    config = load_config()
    answer = call_llm(question, config)
    
    result = {
        "answer": answer,
        "tool_calls": []
    }
    
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
