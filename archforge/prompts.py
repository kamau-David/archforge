"""
prompts.py — builds the prompts sent to Gemini for each module
investigation, and for the final synthesis step.

Gemini cannot open files on its own, so the source code of each module is
read here and placed directly inside the prompt, with line numbers so the
model can cite file:line accurately.
"""

from pathlib import Path

# Keep each module's prompt a sensible size (roughly 40k tokens at most), which
# also keeps us inside the free tier's tokens-per-minute limit.
MAX_CHARS_PER_FILE = 40_000
MAX_CHARS_PER_MODULE = 150_000


def _read_module_source(file_list: list, repo_path) -> tuple:
    """
    Reads every file in the module and returns (source_block, skipped_files).
    Each line is prefixed with its line number.
    """
    blocks = []
    skipped = []
    used = 0

    for rel_path in file_list:
        try:
            text = (Path(repo_path) / rel_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            skipped.append(rel_path)
            continue

        truncated = len(text) > MAX_CHARS_PER_FILE
        if truncated:
            text = text[:MAX_CHARS_PER_FILE]

        if used + len(text) > MAX_CHARS_PER_MODULE:
            skipped.append(rel_path)
            continue
        used += len(text)

        numbered = "\n".join(
            f"{number:>4}: {line}" for number, line in enumerate(text.splitlines(), start=1)
        )
        note = " (only the first part is shown, the file is long)" if truncated else ""
        blocks.append(f"=== FILE: {rel_path}{note} ===\n{numbered}")

    return "\n\n".join(blocks), skipped


def build_module_prompt(module_name: str, file_list: list, repo_context: str = "",
                        repo_path=None) -> str:
    """
    Builds the investigation prompt for a single detected module.
    file_list should be relative paths (as returned by module_detector).
    repo_path is the folder the files live in, so their contents can be included.
    """
    skipped = []
    if repo_path is not None:
        source_block, skipped = _read_module_source(file_list, repo_path)
    else:
        source_block = "\n".join(f"- {f}" for f in file_list)

    skipped_note = ""
    if skipped:
        skipped_note = (
            "\n\nThese files belong to the module but were NOT included (too large or "
            "unreadable), so do not describe their contents:\n"
            + "\n".join(f"- {f}" for f in skipped)
        )

    return f"""You are investigating the "{module_name}" module of a codebase{(' (' + repo_context + ')') if repo_context else ''}.

The full source code of the module is below. Each line starts with its line number.

{source_block}{skipped_note}

Your task: analyze this module and produce a structured report a new developer could read to understand it in under 2 minutes.

Investigate:
- What this module actually does and why it's structured this way
- Key functions/classes and how data flows through them
- Anything fragile, outdated, or worth flagging as tech debt — cite specific files and line numbers

Rules:
- Base every statement only on the code shown above. Do not guess about code you were not given.
- Only cite line numbers that appear in the listing. If you are not sure of a line number, cite the file and function name instead.
- If something is unclear from this module alone, say so rather than inventing an explanation.

Output in this exact structure:

Module: {module_name}
Purpose: [1-2 sentence summary]
Key files: [list the files you actually used]
Data flow: [how data/state moves through this module, in plain steps]
Notable risks/tech debt: [specific, cite file:line where possible]
Confidence: [low/medium/high]"""


def build_synthesis_prompt(module_reports: dict) -> str:
    """
    Builds the final prompt that asks Gemini to synthesize all individual
    module reports into one combined onboarding document.
    module_reports: dict of {module_name: raw_report_text}
    """
    joined_reports = "\n\n---\n\n".join(
        f"### Report for module: {name}\n{report}"
        for name, report in module_reports.items()
    )

    return f"""Below are independent investigation reports for each module of a codebase, already completed:

{joined_reports}

Synthesize these into ONE combined onboarding document with this structure:

# Onboarding Guide

## 60-Second Overview
[3 sentences: what this app/codebase does, core architecture]

## Module Map
[One section per module, using the reports above — do not just copy them verbatim, synthesize and tighten]

## Data Flow Diagram
[Describe how the modules connect to each other, in Mermaid graph TD syntax, inside a mermaid code fence]

## Known Risk Areas (Ranked by Severity)
[Consolidated list across all modules, ranked critical/medium/low, with file:line citations preserved from the reports above]

## Where to Start
[For at least 4 common developer tasks, name the first file to open and why, based on the reports above]

Use only information from the reports above. Do not add file names, line numbers or claims that are not in them.
Write the document directly as markdown. Do not wrap the whole document in a code fence (the Mermaid diagram keeps its own mermaid fence)."""


if __name__ == "__main__":
    sample_prompt = build_module_prompt(
        "lib (top-level)",
        ["lib/main.dart", "lib/feed.dart"],
        repo_context="Fluttergram, a Flutter/Firebase Instagram clone",
    )
    print(sample_prompt)