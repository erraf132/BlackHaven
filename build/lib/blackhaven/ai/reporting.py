from __future__ import annotations

import json
import os
from typing import Dict

from openai import OpenAI

from blackhaven.utils.env import load_dotenv
from blackhaven.utils.storage import save_report_bundle


def _get_client() -> OpenAI:
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or environment.")
    return OpenAI(api_key=api_key)


def _build_prompt(context: Dict[str, str]) -> str:
    return (
        "You are an OSINT report generator. Create a professional investigation report. "
        "Use only authorized testing context. Provide sections: Executive Summary, Scope, "
        "Findings, Risk Assessment, Recommendations, and Next Steps.\n\n"
        f"Target: {context.get('target', '')}\n"
        f"Scope: {context.get('scope', '')}\n"
        f"Findings: {context.get('findings', '')}\n"
        f"Artifacts: {context.get('artifacts', '')}\n"
        f"Notes: {context.get('notes', '')}\n"
    )


def generate_report(context: Dict[str, str]) -> Dict[str, str]:
    client = _get_client()
    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    prompt = _build_prompt(context)

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=900,
    )

    text = getattr(response, "output_text", None)
    if not text:
        text = "Report generation failed."

    report_txt = text.strip()
    report_md = "# BlackHaven Investigation Report\n\n" + report_txt
    report_json = json.dumps({"report": report_txt, **context}, indent=2)

    save_report_bundle("ai_report", report_txt, report_md, report_json)
    return {
        "txt": report_txt,
        "md": report_md,
        "json": report_json,
    }
