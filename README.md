# ArchForge

**Legacy Code Archaeologist** — turns any undocumented codebase into a full onboarding guide, automatically, using [IBM Bob 2.0](https://bob.ibm.com).

Built for the **IBM Bob 2.0 Hackathon**.

---

## The problem

Every developer eventually inherits a codebase with zero documentation, no architecture notes, and the original author long gone. Understanding "what does this do and why" can take days — pure overhead, not progress. This is one of the most common, most expensive problems in software development, and almost no tooling addresses it directly.

## The solution

ArchForge is a fully automated pipeline: point it at any public GitHub repository, and it produces a rendered HTML onboarding guide — no manual review required to get the first draft.

```
clone → detect modules → Bob investigates each module → synthesize → HTML report
```

1. **Clone** — pulls the target repo locally
2. **Detect modules** — automatically groups the repo's files into logical modules based on folder structure
3. **Bob investigates** — for each module, [IBM Bob 2.0](https://bob.ibm.com) (via Bob Shell) is given the exact files in scope and autonomously investigates purpose, data flow, and risks
4. **Synthesize** — a final Bob call merges every module's findings into one coherent document, resolving overlaps and ranking risks by severity
5. **Deliver** — a styled HTML report with an embedded Mermaid architecture diagram, a ranked risk list, and a "where to start" guide for common developer tasks

## How this uses IBM Bob 2.0

ArchForge is built around Bob 2.0's agentic capabilities as the core engine, not as a coding assistant bolted onto a separately-built app:

- **Subagents** — each detected module gets its own independent Bob investigation
- **Parallel / multi-step tasks** — a 10-module repo means 10 separate investigations plus a synthesis call, not one linear pass
- **Agent mode** — Bob autonomously reads source, traces data flow, and flags risks without being told which lines to look at
- **Document understanding** — Bob incorporates existing READMEs, code comments, and open GitHub issues into its analysis instead of ignoring them

## Verified, not just plausible

We didn't just trust the output — we independently checked it against the real source code of both test repositories: exact line numbers, function names, package versions, and code comments. Every claim checked out.

One example, found unprompted by Bob and confirmed against the real source:

> A "Retry" button in [Conduit](https://github.com/cogwheel0/conduit) doesn't actually retry anything — it calls `markNeedsBuild()` instead of recreating the failed `Future`, so tapping retry just redraws the same error.
> — `lib/shared/widgets/error_boundary.dart:182`

## Tested on two real, structurally different repos

| Repo | Description | Result |
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
│   ├── module_detector.py       # auto-groups repo files into logical modules
│   ├── prompts.py               # builds per-module and synthesis prompts for Bob
│   ├── bob_runner.py            # invokes Bob Shell non-interactively
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
- [Bob Shell](https://bob.ibm.com) installed and on your `PATH` (`bob --version` should work)
- A Bob API key, set as `BOB_API_KEY` in a `.env` file in the project root

**Setup:**

```bash
git clone https://github.com/kamau-David/archforge.git
cd archforge
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
BOB_API_KEY=your-api-key-here
```

**Run:**

```bash
python main.py https://github.com/<owner>/<repo>.git
```

The finished report is saved to `output/<repo-name>_onboarding_<timestamp>.html` — open it directly in a browser.

## Known limitations

- Module detection is folder-structure-based, not true code-understanding — it works well for conventionally organized repos but won't distinguish an app's real feature boundaries as precisely as a human would
- It doesn't currently separate application code from tests/tooling folders (e.g. `test/`, `tool/` are treated as modules like any other)
- Windows command-line length limits required a workaround (long prompts are written to a temp file and passed to Bob via `@file` reference rather than inline)

## License

MIT