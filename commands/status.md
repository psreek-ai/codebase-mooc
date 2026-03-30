---
description: Show full status of the Codebase MOOC in this project — components mapped, curriculum generated, review queue, active learners.
argument-hint: ""
allowed-tools: Read, Bash(find:*, python3:*)
---

# /codebase-mooc:status

Check that .codebase-mooc/ exists. If not, say "Codebase MOOC not
initialised in this project. Run /codebase-mooc:init to set it up."
and stop.

Gather and report the following:

## Configuration

Read .codebase-mooc/config.json and report:
- Language and framework
- Codebase size
- Installation date

## Codebase Memory

Check .codebase-mooc/memory/codebase/graph.json:
- Does it exist? If not: "Not yet generated — run /codebase-mooc:generate"
- If yes: report last_updated timestamp and number of components

## Curriculum

Count files in each layer directory:
  .codebase-mooc/memory/curriculum/architecture/
  .codebase-mooc/memory/curriculum/domain/
  .codebase-mooc/memory/curriculum/implementation/
  .codebase-mooc/memory/curriculum/decision_log/
  .codebase-mooc/memory/curriculum/failure_modes/
  .codebase-mooc/memory/curriculum/exercises/

For each layer, report: total files, how many have review_status "approved".

## Review queue

Read .codebase-mooc/memory/human_review_queue.jsonl
Count: pending, processed, total.
If any pending: "Run /codebase-mooc:review to process them."

## Coordinator queue

Read .codebase-mooc/memory/coordinator_queue.jsonl
Count pending events. Report if any are queued.

## Learners

Find all files in .codebase-mooc/memory/learners/
For each learner file, read and report:
  - Learner ID
  - Current arc
  - Competencies mastered count
  - Last session date (from last_updated)

## Format

Present as a clean structured report. Example:

  Codebase MOOC Status
  ──────────────────────────────────────
  Project:      my-service (Python / FastAPI / medium)
  Installed:    2026-03-01

  Codebase Memory
    Components:   23 mapped
    Last updated: 2026-03-28 14:32

  Curriculum
    Architecture:     23 generated, 21 approved
    Implementation:   18 generated, 16 approved
    Decision log:     23 generated, 19 approved
    Failure modes:    12 generated, 10 approved
    Exercises:        47 generated, 40 approved

  Review queue:   4 pending  → /codebase-mooc:review

  Learners
    priya-sharma   Domain Mastery arc   14 competencies mastered
    james-okonkwo  System Literacy arc   6 competencies mastered
