"""
prompts.py — builds the actual prompts sent to Bob Shell for each module
investigation, and the final synthesis step.
"""


def build_module_prompt(module_name: str, file_list: list, repo_context: str = "") -> str:
    """
    Builds the investigation prompt for a single detected module.
    file_list should be relative paths (as returned by module_detector).
    """
    files_block = "\n".join(f"- @{f}" for f in file_list)

    return f"""You are investigating the "{module_name}" module of this codebase{(' (' + repo_context + ')') if repo_context else ''}.

Files in this module:
{files_block}

Your task: analyze this module and produce a structured report a new developer could read to understand it in under 2 minutes.

Investigate:
- What this module actually does and why it's structured this way
- Key functions/classes and how data flows through them
- Anything fragile, outdated, or worth flagging as tech debt — cite specific files and line numbers where possible

Output in this exact structure:

Module: {module_name}
Purpose: [1-2 sentence summary]
Key files: [list the files you actually inspected]
Data flow: [how data/state moves through this module, in plain steps]
Notable risks/tech debt: [specific, cite file:line where possible]
Confidence: [low/medium/high]

Enclose your entire answer in markdown code fences so it can be parsed programmatically."""


def build_synthesis_prompt(module_reports: dict) -> str:
    """
    Builds the final prompt that asks Bob to synthesize all individual
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

Enclose your entire answer in markdown code fences."""


if __name__ == "__main__":
    sample_prompt = build_module_prompt(
        "lib (top-level)",
        ["lib/main.dart", "lib/feed.dart"],
        repo_context="Fluttergram, a Flutter/Firebase Instagram clone",
    )
    print(sample_prompt)