"""
main.py — ArchForge entry point.

Usage:
    py main.py <github_repo_url>

Example:
    py main.py https://github.com/mdanics/fluttergram.git
"""

import sys
import time

from archforge.cloner import clone_repo
from archforge.module_detector import detect_modules
from archforge.prompts import build_module_prompt, build_synthesis_prompt
from archforge.gemini_runner import run_gemini, clean_reply
from archforge.report_builder import build_report


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

    # 3. Investigate each module with Gemini
    module_reports = {}
    repo_name = repo_path.name

    for i, (module_name, files) in enumerate(modules.items(), start=1):
        print(f"[main] ({i}/{len(modules)}) Investigating module: {module_name} ...")
        # The module's source code is read from repo_path and placed in the prompt.
        prompt = build_module_prompt(module_name, files, repo_context=repo_name,
                                     repo_path=repo_path)
        module_reports[module_name] = clean_reply(run_gemini(prompt))
        print(f"[main]     done.\n")
        time.sleep(2)  # small buffer between calls (helps with free-tier rate limits)

    # 4. Synthesize
    print("[main] Synthesizing final onboarding report...")
    synthesis_prompt = build_synthesis_prompt(module_reports)
    final_report_text = clean_reply(run_gemini(synthesis_prompt))
    print("[main]     done.\n")

    # 5. Build final output file
    output_path = build_report(repo_name, module_reports, final_report_text)
    print(f"=== Done. Report saved to: {output_path} ===\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py main.py <github_repo_url>")
        sys.exit(1)

    run_pipeline(sys.argv[1])