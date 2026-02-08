from __future__ import annotations

import os
from typing import List, Tuple

from openai import OpenAI

from blackhaven.utils.env import load_dotenv


_SYSTEM_PROMPT = (
    "You are BlackHaven AI, an elite cyber intelligence assistant. "
    "Answer security questions, analyze domains and IP addresses, "
    "suggest recon steps, and explain vulnerabilities. "
    "Provide concise, actionable guidance with safe, legal boundaries. "
    "Never encourage unauthorized access."
)


def _build_prompt(history: List[Tuple[str, str]]) -> str:
    chunks = [_SYSTEM_PROMPT, "\nConversation:\n"]
    for role, text in history:
        label = "User" if role == "user" else "Assistant"
        chunks.append(f"{label}: {text}")
    chunks.append("Assistant:")
    return "\n".join(chunks)


def _get_client() -> OpenAI:
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or environment.")
    return OpenAI(api_key=api_key)


def ask_ai(question: str, history: List[Tuple[str, str]]) -> str:
    client = _get_client()
    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    prompt = _build_prompt(history + [("user", question)])

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=600,
    )

    text = getattr(response, "output_text", None)
    if text:
        return text.strip()

    output = getattr(response, "output", [])
    if output:
        for item in output:
            if item.get("type") == "message":
                content = item.get("content", [])
                for part in content:
                    if part.get("type") == "output_text":
                        return part.get("text", "").strip()
    return "No response returned by AI."


def run_chat() -> None:
    history: List[Tuple[str, str]] = []
    print("BlackHaven AI > Type 'exit' to return to the menu.")
    while True:
        try:
            question = input("BlackHaven AI > ").strip()
        except EOFError:
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit", "back"}:
            break
        answer = ask_ai(question, history)
        history.append(("user", question))
        history.append(("assistant", answer))
        print(answer)
