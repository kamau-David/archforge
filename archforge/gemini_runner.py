"""
gemini_runner.py — sends prompts to Google's Gemini API and returns the
response text. Replaces bob_runner.py.

Gemini is a plain language model: unlike Bob Shell it cannot open files on
disk by itself, so prompts.py puts the source code directly into the prompt.

Setup:
    1. Get a free API key from Google AI Studio (https://aistudio.google.com).
    2. Put it in your .env file:   GEMINI_API_KEY=your-key-here
    3. (Optional) choose a model:  GEMINI_MODEL=gemini-2.5-flash
"""

import os
import re
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 5


def _get_settings():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "[gemini_runner] GEMINI_API_KEY is not set. Create a key in Google "
            "AI Studio and add this line to your .env file:\n"
            "GEMINI_API_KEY=your-key-here"
        )
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    return api_key, model


def _retry_delay(response: requests.Response, attempt: int) -> int:
    """Seconds to wait before retrying. Honors Retry-After when the API sends it."""
    header = response.headers.get("Retry-After", "")
    if header.isdigit():
        return int(header)
    # Free-tier limits are per minute, so back off in fairly big steps.
    return min(65, 15 * attempt)


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "unknown")
        raise RuntimeError(f"[gemini_runner] Gemini returned no answer (reason: {reason}).")

    candidate = candidates[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()

    if not text:
        finish = candidate.get("finishReason", "unknown")
        raise RuntimeError(f"[gemini_runner] Gemini returned an empty answer (finishReason: {finish}).")

    if candidate.get("finishReason") == "MAX_TOKENS":
        print("[gemini_runner] Warning: the answer hit the output limit and may be cut off.")

    return text


# Models sometimes wrap the whole answer in one ```markdown ... ``` fence even
# when told not to. Strip that outer fence so the report renders as a document
# instead of a code block. Inner fences (e.g. ```mermaid) are left alone.
_OUTER_FENCE = re.compile(r"^```(?:markdown|md|text)?[ \t]*\n(.*)\n```$", re.DOTALL)


def clean_reply(text: str) -> str:
    text = text.strip()
    match = _OUTER_FENCE.match(text)
    return match.group(1).strip() if match else text


def run_gemini(prompt: str, timeout: int = 300, temperature: float = 0.2) -> str:
    """
    Sends one prompt to Gemini and returns the answer as a string.
    Retries automatically when the API says "slow down" (HTTP 429) or is busy.
    """
    api_key, model = _get_settings()
    url = API_URL.format(model=model)
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, json=body, timeout=timeout)
        except requests.Timeout:
            raise RuntimeError(f"[gemini_runner] Gemini call timed out after {timeout}s")
        except requests.RequestException as exc:
            raise RuntimeError(f"[gemini_runner] Could not reach the Gemini API: {exc}")

        if response.status_code == 200:
            return _extract_text(response.json())

        if response.status_code in (429, 500, 503):
            # A daily quota will not recover by waiting a minute, so stop early.
            if response.status_code == 429 and re.search(r"per ?day", response.text, re.I):
                raise RuntimeError(
                    "[gemini_runner] Your daily Gemini quota is used up. Try again "
                    "tomorrow, or set GEMINI_MODEL to a different model.\n"
                    f"{response.text[:300]}"
                )
            wait = _retry_delay(response, attempt)
            print(
                f"[gemini_runner] Gemini said {response.status_code} "
                f"(attempt {attempt}/{MAX_RETRIES}). Waiting {wait}s..."
            )
            time.sleep(wait)
            continue

        raise RuntimeError(
            f"[gemini_runner] Gemini API error {response.status_code}:\n{response.text[:500]}"
        )

    raise RuntimeError(
        f"[gemini_runner] Gemini was still busy or rate-limited after {MAX_RETRIES} attempts."
    )


if __name__ == "__main__":
    print("[gemini_runner] Testing Gemini connection...\n")
    print("Gemini responded:")
    print(run_gemini("Reply with exactly the word: OK"))