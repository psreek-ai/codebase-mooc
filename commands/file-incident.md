---
description: File a post-mortem or incident report for curriculum processing. The Pathologist agent generates a failure mode curriculum entry from it.
argument-hint: "<path-to-incident-file>"
allowed-tools: Read, Write, Bash(python3:*)
---

# /codebase-mooc:file-incident

$ARGUMENTS should contain the path to the incident report or post-mortem
markdown file.

If $ARGUMENTS is empty, ask: "What is the path to the incident report
or post-mortem file?"

Check that the file exists using the Read tool.
If it does not exist, say "File not found: <path>" and stop.

Check that .codebase-mooc/memory/ exists.
If not, say "Run /codebase-mooc:init first." and stop.

Read the first 200 characters of the incident file to get a preview.

Append to .codebase-mooc/memory/coordinator_queue.jsonl:

{
  "event_type": "incident_filed",
  "workflow": "pathologist_run",
  "priority": "high",
  "incident_file": "<absolute path to the file>",
  "preview": "<first 200 chars>",
  "filed_at": "<iso timestamp>"
}

Then invoke the pathologist agent with:
  --incident-file <path>

After the pathologist completes, invoke the reviewer agent.

After the reviewer completes, read the human review queue and report:
- That a failure mode entry has been generated
- That it is in the human review queue
- That it will go live in the curriculum after approval
- How to review it: /codebase-mooc:review
