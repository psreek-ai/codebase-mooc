---
description: Open the human review queue. Shows flagged curriculum content with Reviewer Agent critique. Approve or reject each item.
argument-hint: ""
allowed-tools: Read, Write
---

# /codebase-mooc:review

Read the human review queue:
  .codebase-mooc/memory/human_review_queue.jsonl

If the file is empty or has no pending items, tell the developer:
"No items pending review." and stop.

Count pending items and say: "N item(s) pending review."

For each pending item, process it one at a time:

## For each item

Read the content file:
  .codebase-mooc/memory/curriculum/{layer}/{component}.json

Read the review annotation if it exists:
  .codebase-mooc/memory/curriculum/review_annotations/{component}_{layer}.json

Present:
1. Component name and layer
2. The Reviewer Agent's flags (all of them, with severity)
3. The content — full text for short items, key sections for long ones
4. The Reviewer's overall recommendation

Ask the developer: "Approve (a), Reject with feedback (r), or Skip (s)?"

**If approved:**
Update the content file: set review_status to "approved"
Add reviewed_at: <timestamp> and human_reviewer: <ask for name once>
Write back to the content file.
Mark the queue item status as "processed".

**If rejected:**
Ask: "What is the rejection reason? This will be sent back to the
generating agent."
Update the content file: set review_status to "rejected",
rejection_reason: <their text>.
Append a new event to coordinator_queue.jsonl:
{
  "event_type": "regeneration_requested",
  "workflow": "regeneration",
  "component": "<n>",
  "layer": "<layer>",
  "feedback": "<rejection reason>",
  "priority": "normal"
}
Mark the queue item status as "processed".

**If skipped:**
Leave the queue item as pending. Move to the next.

## After all items

Report:
- Approved: N
- Rejected and queued for regeneration: N
- Skipped: N

If any were rejected, say: "Rejected items will be regenerated with
your feedback. The coordinator will process them in the background."
