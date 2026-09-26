"""
report_builder.py — takes module reports + the final synthesis text
and writes them to a markdown file in output/.
(HTML formatting comes as a polish step once the pipeline is proven.)
"""

from pathlib import Path
from datetime import datetime


def build_report(repo_name: str, module_reports: dict, final_report_text: str) -> Path:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"{repo_name}_onboarding_{timestamp}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_report_text)
        f.write("\n\n---\n\n## Raw Per-Module Reports (unedited)\n\n")
        for module_name, report in module_reports.items():
            f.write(f"### {module_name}\n\n{report}\n\n---\n\n")

    return output_path