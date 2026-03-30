# Codebase MOOC

AI-generated engineering education embedded in your codebase.
Takes any developer from novice to owner without going anywhere else.

## Install

In Claude Code:

```
/plugin install codebase-mooc@claude-plugins-official
```

## Use

Open any project in Claude Code and say:

> "Set up the codebase MOOC for this project"

That is the only instruction needed. The plugin detects your language
and framework, builds a structured map of the codebase, generates the
full curriculum across six layers, and starts watching every commit
for changes that require curriculum updates.

To start a learning session for a developer:

> "Start a learning session for Priya"

## What it generates

The curriculum has six layers, each serving a different learning purpose:

**Architecture layer** — the map before the territory. What the system
does, how it is structured, and where each component sits before a new
developer reads a single line of code.

**Domain layer** — the business logic and why it exists. The regulatory
requirements, the user behaviour patterns, the commercial constraints
that shaped the code.

**Implementation layer** — deep walkthroughs of critical code. Not what
the code does — why it does it that way, what breaks if you change it,
what a developer must understand before touching it.

**Decision log** — the road not taken. Every significant architectural
decision: what was chosen, what alternatives were available, what
constraints ruled them out. Extracted from git history and code shape.

**Failure mode archive** — every incident turned into a lesson. What
happened, what the system's design made possible, how to recognise the
same failure early. Plus proactive analysis of failure modes that have
not yet manifested.

**Exercise layer** — gamified assessments that require genuine
understanding. Competency-gated progression through six arcs: Orientation,
Foundations, System Literacy, Domain Mastery, Engineering Judgment,
Contribution, and Ownership. Boss levels at the end of each arc.

The curriculum is committed to your repository alongside your code and
stays synchronised with it automatically. Every commit is watched.
Every significant change triggers a curriculum update in the background.

## Commands

| Command | What it does |
|---|---|
| `/codebase-mooc:init` | First-time setup in a project |
| `/codebase-mooc:generate` | Run the full curriculum generation pipeline |
| `/codebase-mooc:learn` | Start or continue a learning session |
| `/codebase-mooc:review` | Process the human review queue |
| `/codebase-mooc:status` | Full status report |
| `/codebase-mooc:file-incident` | File an incident for curriculum processing |

## Skills (auto-activating)

Three skills activate automatically based on context — no commands needed:

**codebase-archaeologist** — activates when debugging unfamiliar code,
explaining how something works, or figuring out where a change belongs.
Reads Codebase Memory and grounds responses in the actual system architecture.

**curriculum-reviewer** — activates when working through the review queue.
Loads the evaluation rubric inline so reviewers have criteria in context.

**learning-tutor** — activates when a developer wants to learn. Reads
their learner state and delivers the right content at the right depth.

## CI/CD integration

For teams that want curriculum updates on every merge to main:

```yaml
# .github/workflows/mooc-update.yml
name: Update Codebase MOOC

on:
  push:
    branches: [main]

jobs:
  update-curriculum:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install anthropic gitpython -q
      - name: Update curriculum
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python3 .codebase-mooc/scripts/coordinator.py --process-queue
      - name: Commit curriculum updates
        run: |
          git config user.name "codebase-mooc"
          git config user.email "mooc@ci"
          git add .codebase-mooc/memory/curriculum/ .codebase-mooc/memory/codebase/
          git diff --staged --quiet || \
            git commit -m "chore(mooc): curriculum update [$(git rev-parse --short HEAD)]"
          git push
```

## Requirements

- Claude Code
- Python 3.9+
- git

## Privacy

Source code and git history from your project are sent to the Anthropic
API during curriculum generation. This is governed by your Anthropic
account's data handling terms.

Learner data is stored locally only. It is gitignored by default and
never leaves the developer's machine.

## Part of the Code & Comprehension series

This plugin is the technical implementation described in the
*Code & Comprehension* series on Medium — a series on AI, engineering
knowledge, and the responsibility we carry toward the developers who
come after us.
