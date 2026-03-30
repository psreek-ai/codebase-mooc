---
description: Show full status of the Codebase MOOC in this project.
argument-hint: ""
allowed-tools: Read, Bash(find:*, python3:*)
---

# /codebase-mooc:status

Check that .codebase-mooc/ exists. If not, say "Not initialised —
run /codebase-mooc:init" and stop.

Report the following:

## Configuration

Read .codebase-mooc/config.json:
- Language, framework, size
- Installation date

## Codebase Memory (JSON)

Read .codebase-mooc/memory/codebase/graph.json:
- If missing: "Not yet generated — run /codebase-mooc:generate"
- If present: last_updated and number of components

## Curriculum (Markdown)

Count .md files in each curriculum directory:
  .codebase-mooc/curriculum/architecture/
  .codebase-mooc/curriculum/implementation/
  .codebase-mooc/curriculum/decision_log/
  .codebase-mooc/curriculum/failure_modes/
  .codebase-mooc/curriculum/exercises/

For each layer, report:
- Total .md files
- How many contain "Review status:** Approved" (approved by a human)
- How many contain "Review status:** Pending" (awaiting review)

## Review queue (JSON)

Read .codebase-mooc/memory/human_review_queue.jsonl
Count pending items. If any: "Run /codebase-mooc:review to process."

## Learners (JSON)

Read all .codebase-mooc/memory/learners/*.json files.
For each: learner_id, current_arc, mastered competency count, last session.

## Format

Present as a clean report. Example:

  Codebase MOOC Status
  ──────────────────────────────────────────────
  Project:     my-service (Python / FastAPI / medium)
  Installed:   2026-03-01

  Codebase Memory
    Components: 23 mapped  |  Last updated: 2026-03-28 14:32

  Curriculum (Markdown — browse at .codebase-mooc/curriculum/)
    Architecture:     23 files  |  21 approved  |  2 pending
    Implementation:   18 files  |  16 approved  |  2 pending
    Decision log:     23 files  |  19 approved  |  4 pending ⚠
    Failure modes:    12 files  |  10 approved  |  2 pending
    Exercises:        47 files  |  40 approved  |  7 pending

  Review queue:  4 pending  →  /codebase-mooc:review

  Learners
    priya-sharma    Domain Mastery      14 competencies mastered
    james-okonkwo   System Literacy      6 competencies mastered
