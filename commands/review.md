---
description: Open the human review queue. Shows flagged Markdown curriculum files with Reviewer Agent critique. Approve or reject each item.
argument-hint: ""
allowed-tools: Read, Write
---

# /codebase-mooc:review

Read the human review queue (JSON):
  .codebase-mooc/memory/human_review_queue.jsonl

If empty or no pending items: "No items pending review." and stop.

For each pending item, process one at a time.

## For each item

The curriculum content is a Markdown file at:
  .codebase-mooc/curriculum/{layer}/{component}.md

The Reviewer Agent's flags are in a JSON annotation file at:
  .codebase-mooc/memory/review_annotations/{component}_{layer}.json

Present:
1. The Markdown file path (so the developer can open it directly)
2. All Reviewer Agent flags with severity
3. A preview of the Markdown content
4. The Reviewer's overall recommendation

Ask: "Approve (a), Reject with feedback (r), or Skip (s)?"

**If approved:**
Update the Markdown file — replace "Review status:** Pending" with
"Review status:** Approved by {reviewer_name} · {today's date}"

Mark the queue item status as "processed" in the JSON queue.

**If rejected:**
Ask: "What is the rejection reason?"
Update the Markdown file — replace "Review status:** Pending" with
"Review status:** Rejected — {reason}"

Append to .codebase-mooc/memory/coordinator_queue.jsonl:
{
  "event_type": "regeneration_requested",
  "workflow": "regeneration",
  "component": "{component}",
  "layer": "{layer}",
  "feedback": "{reason}",
  "priority": "normal"
}

Mark the queue item status as "processed".

**If skipped:**
Leave as pending. Move to next.

## After all items

Report: Approved N, Rejected N, Skipped N.
If any rejected: "Rejected items will be regenerated with your feedback."
