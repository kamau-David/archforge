"""
main.py — ArchForge entry point.

Usage:
    py main.py <github_repo_url>

Example:
    py main.py https://github.com/mdanics/fluttergram.git
"""

import re
import sys
import time
from pathlib import Path

from archforge.cloner import clone_repo
from archforge.module_detector import detect_modules
from archforge.prompts import build_module_prompt, build_synthesis_prompt
from archforge.bob_runner import run_bob
from archforge.report_builder import build_report


def extract_assistant_reply(raw_bob_output: str) -> str:
    """
    Bob's CLI output may contain multiple 'Assistant (N)' segments when it
    makes tool calls along the way (e.g. 'Let me explore...' before the
    real report). We want the LAST assistant segment — the final answer
    after all tool calls have resolved.
    """
    segments = re.split(r'\n─+\n', raw_bob_output)

    assistant_segments = []
    for seg in segments:
        stripped = seg.strip()
        if stripped.startswith("Assistant ("):
            lines = stripped.splitlines()
            content = "\n".join(lines[1:]).strip()  # drop the "Assistant (N) <timestamp>" header
            assistant_segments.append(content)

    reply = assistant_segments[-1] if assistant_segments else raw_bob_output.strip()

    # Strip terminal OSC-8 hyperlink escape sequences. Bob's CLI makes file
    # paths clickable in a real terminal using the form:
    #   ]8;;<url>\<label>]8;;\
    # (sometimes with real ESC/BEL bytes, sometimes just the visible
    # "]8;;" text when the terminal doesn't render them). As captured
    # plain text these leak through as garbage — keep just the label.
    reply = re.sub(r'\]8;;[^\\]*\\([^\]]*)\]8;;\\?', r'\1', reply)
    reply = re.sub(r'\x1b\]8;;[^\x07\x1b]*(?:\x07|\x1b\\)', '', reply)

    return reply


def run_pipeline(repo_url: str):
    print(f"\n=== ArchForge: analyzing {repo_url} ===\n")

    # 1. Clone
    repo_path = clone_repo(repo_url)

    # 2. Detect modules
    print("\n[main] Detecting modules...")
    modules = detect_modules(repo_path)
    print(f"[main] Found {len(modules)} module(s): {', '.join(modules.keys())}\n")

    if not modules:
        print("[main] No modules detected — nothing to analyze. Exiting.")
        return

    # 3. Investigate each module with Bob
    module_reports = {}
    repo_name = repo_path.name

    for i, (module_name, files) in enumerate(modules.items(), start=1):
        print(f"[main] ({i}/{len(modules)}) Investigating module: {module_name} ...")
        prompt = build_module_prompt(module_name, files, repo_context=repo_name)

        # Bob needs to run with the repo folder as its working context —
        # we pass file paths relative to repo_path, but the @file references
        # need to resolve from inside repo_path.
        raw_output = run_bob(prompt, cwd=repo_path)
        module_reports[module_name] = extract_assistant_reply(raw_output)
        print(f"[main]     done.\n")
        time.sleep(1)  # small buffer between calls

    # 4. Synthesize
    print("[main] Synthesizing final onboarding report...")
    synthesis_prompt = build_synthesis_prompt(module_reports)
    raw_synthesis = run_bob(synthesis_prompt, cwd=repo_path)
    final_report_text = extract_assistant_reply(raw_synthesis)
    print("[main]     done.\n")

    # 5. Build final output file
    output_path = build_report(repo_name, module_reports, final_report_text)
    print(f"=== Done. Report saved to: {output_path} ===\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py main.py <github_repo_url>")
        sys.exit(1)

    run_pipeline(sys.argv[1])