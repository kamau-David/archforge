"""
bob_runner.py — wraps calls to Bob Shell's non-interactive mode
(`bob -p "..."`) and captures the response as text.
"""

import subprocess
import platform
import uuid
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Windows command-line length limit is ~8191 chars. Stay well under that
# before switching to the file-reference approach.
MAX_INLINE_PROMPT_LENGTH = 3000


def _run_bob_command(prompt: str, timeout: int, cwd: Optional[Path]) -> str:
    is_windows = platform.system() == "Windows"

    try:
        result = subprocess.run(
            ["bob", "-p", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=is_windows,
            cwd=str(cwd) if cwd else None,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"[bob_runner] Bob call timed out after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(
            "[bob_runner] 'bob' command not found. Is Bob Shell installed "
            "and on your PATH? Try running 'bob --version' manually to check."
        )

    if result.returncode != 0:
        raise RuntimeError(f"[bob_runner] Bob exited with an error:\n{result.stderr}")

    return result.stdout.strip()


def run_bob(prompt: str, timeout: int = 300, cwd: Optional[Path] = None) -> str:
    """
    Runs a single non-interactive Bob Shell prompt and returns its
    stdout as a string. If cwd is given, Bob runs with that directory
    as its working context (so @file references resolve correctly).

    Long prompts are automatically written to a temp file inside cwd
    and passed to Bob via @filename, to avoid Windows' command-line
    length limit.
    """
    if len(prompt) <= MAX_INLINE_PROMPT_LENGTH:
        return _run_bob_command(prompt, timeout, cwd)

    base_dir = Path(cwd) if cwd else Path.cwd()
    temp_filename = f"_archforge_prompt_{uuid.uuid4().hex}.txt"
    temp_path = base_dir / temp_filename

    temp_path.write_text(prompt, encoding="utf-8")
    try:
        short_prompt = (
            f"Read the file @{temp_filename} — it contains your full task "
            f"instructions. Follow them exactly and produce the requested output."
        )
        return _run_bob_command(short_prompt, timeout, cwd)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    print("[bob_runner] Testing Bob Shell connection...\n")
    response = run_bob("Reply with exactly the word: OK")
    print("Bob responded:")
    print(response)