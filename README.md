# ArchForge

**Legacy Code Archaeologist** — turns undocumented codebases into onboarding guides, automatically, using AI.

ArchForge was built for the **IBM Bob 2.0 Hackathon** using [IBM Bob 2.0](https://bob.ibm.com) as its analysis engine. It now runs on **Google Gemini**, so anyone with a free Gemini API key can run it. The original Bob version is still in this repository's git history.

---

## The problem

Every developer eventually inherits a codebase with zero documentation, no architecture notes, and the original author long gone. Understanding "what does this do and why" can take days — pure overhead, not progress. This is one of the most common, most expensive problems in software development, and almost no tooling addresses it directly.

## The solution

ArchForge is an automated pipeline: point it at a public GitHub repository, and it produces a rendered HTML onboarding guide, so you get a first draft without reading the whole codebase yourself.

```
clone → detect modules → Gemini analyzes each module → synthesize → HTML report
```

1. **Clone** — pulls the target repo locally
2. **Detect modules** — groups the repo's files into logical modules based on folder structure
3. **Analyze** — for each module, the source code (with line numbers) is sent to Gemini, which reports on purpose, data flow, and risks
4. **Synthesize** — a final call merges every module's findings into one document, resolving overlaps and ranking risks by severity
5. **Deliver** — a styled HTML report with an embedded Mermaid architecture diagram, a ranked risk list, and a "where to start" guide for common developer tasks

## Hackathon version (IBM Bob 2.0)

The hackathon version used Bob Shell as an agent: one Bob investigation per detected module (subagents), multi-step tasks, and Bob reading the files itself. The results below come from that version.

## Verified, not just plausible

For the Bob version, I checked the output against the real source code of both test repositories: line numbers, function names, package versions, and code comments. Every claim I checked held up.

One example, found by Bob and confirmed against the real source:

> A "Retry" button in [Conduit](https://github.com/cogwheel0/conduit) doesn't actually retry anything — it calls `markNeedsBuild()` instead of recreating the failed `Future`, so tapping retry just redraws the same error.
> — `lib/shared/widgets/error_boundary.dart:182`

The Gemini version has not yet been checked the same way, and AI output can contain mistakes, so treat the reports as a starting point and verify important findings in the code.

## Tested on two real, structurally different repos

| Repo | Description | Result (Bob version) |
|---|---|---|
| [mdanics/fluttergram](https://github.com/mdanics/fluttergram) | Flat, undocumented, ~2018-era Flutter/Firebase app | 3 modules detected, 12+ findings verified |
| [cogwheel0/conduit](https://github.com/cogwheel0/conduit) | Modern, feature-organized Riverpod/Drift AI chat client | 10 modules detected, 18+ findings verified |

Sample generated reports for both are in [`examples/`](./examples).

## Project structure

```
archforge/
├── main.py                     # CLI entry point — runs the full pipeline
├── archforge/
│   ├── cloner.py                # clones a target GitHub repo
│   ├── module_detector.py       # groups repo files into logical modules
│   ├── prompts.py               # builds per-module and synthesis prompts
│   ├── gemini_runner.py         # calls the Gemini API (with retries)
│   └── report_builder.py        # renders the final HTML onboarding guide
├── templates/
│   └── onboarding_report.html   # HTML/CSS template
├── examples/
│   ├── fluttergram_onboarding_report.html
│   └── conduit_onboarding_report.html
├── requirements.txt
└── README.md
```

## Running it yourself

**Requirements:**
- Python 3.10+
- Git installed and on your `PATH`
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com)

**Setup:**

```bash
git clone https://github.com/kamau-David/archforge.git
cd archforge
python -m venv venv
```

Activate the virtual environment:

```bash
venv\Scripts\Activate.ps1      # Windows PowerShell
source venv/bin/activate       # macOS / Linux
```

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-api-key-here
# Optional: choose a different model (default is gemini-2.5-flash)
# GEMINI_MODEL=gemini-2.5-pro
```

Check the connection:

```bash
python -m archforge.gemini_runner
```

**Run:**

```bash
python main.py https://github.com/<owner>/<repo>.git
```

The finished report is saved to `output/<repo-name>_onboarding_<timestamp>.html` — open it directly in a browser.

## Known limitations

- Module detection is folder-structure-based, not true code-understanding — it works well for conventionally organized repos but won't distinguish an app's real feature boundaries as precisely as a human would
- It doesn't currently separate application code from tests/tooling folders (e.g. `test/`, `tool/` are treated as modules like any other)
- Gemini only sees the code placed in each prompt. Very large files are cut off and very large modules have some files left out; the report notes which files were skipped
- Free-tier Gemini keys have per-minute and per-day limits, so big repos may pause between calls or stop when the daily quota runs out
- Reports are AI-generated and can contain errors

## License

MIT
