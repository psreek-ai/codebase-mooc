---
description: First-time setup of the Codebase MOOC in this project. Creates directory structure, detects codebase profile, and prepares for curriculum generation. Safe to re-run.
argument-hint: ""
allowed-tools: Read, Write, Bash(find:*, python3:*, git:rev-parse:*)
---

# /codebase-mooc:init

Run this sequence exactly. Do not skip steps.

## Step 1 — Check Python

Run: python3 --version

If Python 3.9 or higher is not available, tell the developer and stop.

## Step 2 — Create directory structure

Two separate directory trees:

**.codebase-mooc/memory/** — internal JSON state (partially gitignored)
**.codebase-mooc/curriculum/** — human-readable Markdown (fully committed)

Run: python3 -c "
import json
from pathlib import Path
from datetime import datetime, timezone

root = Path.cwd()
mooc = root / '.codebase-mooc'

# Internal JSON state directories
memory_dirs = [
    'memory/codebase',
    'memory/review_annotations',
    'memory/learners',
    'memory/agent_logs',
    'scripts/setup',
    'scripts/review',
]

# Human-readable Markdown curriculum directories
curriculum_dirs = [
    'curriculum/architecture',
    'curriculum/implementation',
    'curriculum/decision_log',
    'curriculum/failure_modes',
    'curriculum/exercises/system_literacy',
    'curriculum/exercises/domain_mastery',
    'curriculum/exercises/engineering_judgment',
    'curriculum/exercises/boss_levels',
]

for d in memory_dirs + curriculum_dirs:
    (mooc / d).mkdir(parents=True, exist_ok=True)

# .gitignore: commit curriculum MD, ignore personal/runtime JSON
gitignore = mooc / 'memory' / '.gitignore'
if not gitignore.exists():
    gitignore.write_text(
        '# Personal and runtime data — stays local\n'
        'learners/\nagent_logs/\ncoordinator_queue.jsonl\n'
        'classify_queue.jsonl\nhuman_review_queue.jsonl\n\n'
        '# Codebase memory and review annotations are committed\n'
        '!codebase/\n!review_annotations/\n'
    )

# Curriculum is fully committed — no gitignore needed there

# Initialise empty queues
for q in ['coordinator_queue.jsonl', 'classify_queue.jsonl',
          'human_review_queue.jsonl']:
    p = mooc / 'memory' / q
    if not p.exists():
        p.write_text('')

print('Structure created')
"

## Step 3 — Detect codebase profile

Scan the project to detect language, framework, monorepo, and size.
Write .codebase-mooc/config.json with the detected values.

Run: python3 .codebase-mooc/scripts/setup/detect_profile.py

## Step 4 — Update root .gitignore

Add these lines to the root .gitignore if not already present:

# Codebase MOOC — personal and runtime data
.codebase-mooc/memory/learners/
.codebase-mooc/memory/agent_logs/
.codebase-mooc/memory/coordinator_queue.jsonl
.codebase-mooc/memory/classify_queue.jsonl
.codebase-mooc/memory/human_review_queue.jsonl

Do NOT ignore .codebase-mooc/curriculum/ — those Markdown files
are committed alongside the code.

## Step 5 — Report

Tell the developer:
- What was detected (language, framework, size)
- That the structure is ready
- The directory layout:
    .codebase-mooc/memory/     → internal JSON state
    .codebase-mooc/curriculum/ → Markdown curriculum (committed to git)
- Next step: /codebase-mooc:generate
- Estimated generation time based on size:
    small=2min, medium=5min, large=15min, xlarge=30min+
