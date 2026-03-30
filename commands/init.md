---
description: First-time setup of the Codebase MOOC in this project. Creates the .codebase-mooc/ directory structure, detects the codebase profile, and prepares the system for curriculum generation. Safe to re-run.
argument-hint: ""
allowed-tools: Read, Write, Bash(find:*, python3:*, git:rev-parse:*)
---

# /codebase-mooc:init

Run this sequence exactly. Do not skip steps. Do not ask for confirmation
between steps unless a step explicitly requires it.

## Step 1 — Check Python

Run: python3 --version

If Python 3.9 or higher is not available, tell the developer and stop.
The harness requires Python 3.9+.

## Step 2 — Create directory structure

Run: python3 -c "
import json
from pathlib import Path
from datetime import datetime, timezone

root = Path.cwd()
mooc = root / '.codebase-mooc'

dirs = [
    'memory/codebase',
    'memory/curriculum/architecture',
    'memory/curriculum/domain',
    'memory/curriculum/implementation',
    'memory/curriculum/decision_log',
    'memory/curriculum/failure_modes',
    'memory/curriculum/exercises/system_literacy',
    'memory/curriculum/exercises/domain_mastery',
    'memory/curriculum/exercises/engineering_judgment',
    'memory/curriculum/exercises/boss_levels',
    'memory/curriculum/review_annotations',
    'memory/learners',
    'memory/agent_logs',
    'scripts/setup',
    'scripts/review',
]

for d in dirs:
    (mooc / d).mkdir(parents=True, exist_ok=True)

# Write memory .gitignore
gitignore = mooc / 'memory' / '.gitignore'
if not gitignore.exists():
    gitignore.write_text(
        'learners/\nagent_logs/\ncoordinator_queue.jsonl\n'
        'classify_queue.jsonl\nhuman_review_queue.jsonl\n\n'
        '!codebase/\n!curriculum/\n'
    )

# Initialise empty queues
for q in ['coordinator_queue.jsonl', 'classify_queue.jsonl',
          'human_review_queue.jsonl']:
    p = mooc / 'memory' / q
    if not p.exists():
        p.write_text('')

print('Structure created')
"

If this fails, show the error and stop.

## Step 3 — Detect codebase profile

Scan the project to detect:

Language detection — count files by extension:
Run: find . -type f -not -path "./.git/*" -not -path "./.codebase-mooc/*" -not -path "*/node_modules/*"

From the file list determine:
- Primary language (by file count: .py, .ts, .js, .java, .go, .rs, .rb)
- Framework (check for: manage.py→django, pom.xml→spring,
  package.json with next→nextjs, go.mod→go-module, Cargo.toml→rust,
  fastapi in requirements.txt→fastapi, flask→flask)
- Monorepo (true if: lerna.json, pnpm-workspace.yaml, turbo.json,
  nx.json, or packages/ + package.json exist together)
- Size (small <200 files, medium <2000, large <20000, xlarge 20000+)

## Step 4 — Write config.json

Write .codebase-mooc/config.json:

{
  "version": "1.0",
  "installed_at": "<iso timestamp>",
  "language": "<detected>",
  "framework": "<detected>",
  "is_monorepo": <boolean>,
  "size": "<small|medium|large|xlarge>",
  "total_files": <int>
}

## Step 5 — Update root .gitignore

Check the root .gitignore. If .codebase-mooc/memory/learners/ is not
already ignored, append:

# Codebase MOOC — personal learner data
.codebase-mooc/memory/learners/
.codebase-mooc/memory/agent_logs/
.codebase-mooc/memory/coordinator_queue.jsonl
.codebase-mooc/memory/classify_queue.jsonl
.codebase-mooc/memory/human_review_queue.jsonl

## Step 6 — Report

Tell the developer:
- What was detected (language, framework, size)
- That the structure is ready
- The next step: run /codebase-mooc:generate to build the curriculum
- That generation takes approximately: small=2min, medium=5min,
  large=15min, xlarge=30min+
