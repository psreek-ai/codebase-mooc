---
description: Run the full curriculum generation pipeline. Sequences all agents and reports progress. Takes 2–30 minutes depending on codebase size.
argument-hint: ""
allowed-tools: Read, Write, Bash(python3:*)
---

# /codebase-mooc:generate

Check that .codebase-mooc/config.json exists. If not, tell the developer
to run /codebase-mooc:init first and stop.

Run the pipeline in this exact sequence. Report each step as it starts.
Stop and report clearly if any step fails.

## Step 1 — Archaeologist

Say: "Running Archaeologist — mapping codebase structure..."

Invoke the archaeologist agent with: --full-run

The archaeologist builds Codebase Memory at:
  .codebase-mooc/memory/codebase/graph.json

When it completes, read that file and report:
- Number of components mapped
- Primary language and framework detected
- Architectural patterns identified

## Step 2 — Architect

Say: "Running Architect — generating architecture layer..."

Invoke the architect agent with: --full-run

When complete, count the files written to:
  .codebase-mooc/memory/curriculum/architecture/

Report: "Architecture layer: N files generated"

## Step 3 — Historian

Say: "Running Historian — extracting decision log..."

Invoke the historian agent with: --full-run

When complete, count files in:
  .codebase-mooc/memory/curriculum/decision_log/

Note how many have requires_human_review: true and report it.

## Step 4 — Instructor

Say: "Running Instructor — building implementation walkthroughs..."

Invoke the instructor agent with: --full-run

When complete, count files in:
  .codebase-mooc/memory/curriculum/implementation/

## Step 5 — Pathologist

Say: "Running Pathologist — building failure mode archive..."

Invoke the pathologist agent with: --full-run

When complete, count files in:
  .codebase-mooc/memory/curriculum/failure_modes/

## Step 6 — Examiner

Say: "Running Examiner — generating exercises and boss levels..."

Invoke the examiner agent with: --full-run

When complete, count files across all exercise arc directories.

## Step 7 — Reviewer

Say: "Running Reviewer — validating generated content..."

Invoke the reviewer agent with: --full-run

Read the human review queue after the reviewer completes:
  .codebase-mooc/memory/human_review_queue.jsonl

Count pending items.

## Final report

Tell the developer:
- Total components processed
- Total curriculum modules generated (sum across all layers)
- Number of items pending human review
- How to process the review queue: /codebase-mooc:review
- How to start a learning session: /codebase-mooc:learn
- That the system will now maintain itself — every commit is watched
