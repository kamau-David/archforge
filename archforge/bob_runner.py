"""
bob_runner.py — wraps calls to Bob Shell's non-interactive mode
(`bob -p "..."`) and captures the response as text.
"""

import subprocess
import platform
from dotenv import load_dotenv

load_dotenv()


def run_bob(prompt: str, timeout: int = 300) -> str:
    """
    Runs a single non-interactive Bob Shell prompt and returns its
    stdout as a string. Raises RuntimeError if Bob exits non-zero
    or the call times out.
    """
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


if __name__ == "__main__":
    print("[bob_runner] Testing Bob Shell connection...\n")
    response = run_bob("Reply with exactly the word: OK")
    print("Bob responded:")
    print(response)