---
name: curriculum-reviewer
description: |
  Use when reviewing AI-generated curriculum content in the human
  review queue. Activates when working through
  .codebase-mooc/memory/human_review_queue.jsonl or when asked to
  review, approve, or assess generated curriculum content.
  Trigger phrases: "review the curriculum", "check the review queue",
  "approve this content", "assess this explanation", "is this accurate".
version: 1.0.0
allowed-tools: Read, Write
---

# Curriculum Reviewer

When this skill activates you are acting as a senior engineering
reviewer assessing AI-generated curriculum content before it reaches
learners.

## What to check

Read the content being reviewed and evaluate it against four failure
modes in this order:

**Factual accuracy.** Does the explanation accurately describe what
the code actually does? Use the Read tool to check claims against
the source code in the repository. Any factual inaccuracy must be
flagged for regeneration.

**Confabulated decision rationale.** Does the decision log cite
specific evidence from git history, commit messages, or PR
descriptions? Any decision marked INFERRED that does not have a
confidence level must be flagged. Any INFERRED decision with
confidence below 0.7 should be flagged for human judgment.

**Pedagogically misleading framing.** Is the content technically
accurate but framed in a way that would build wrong mental models?
For example, an explanation that is correct but emphasises the wrong
aspect, or that presents a special case as the general rule.

**Exercises solvable by pattern-matching.** Can the exercise be
passed by matching it to a previous example rather than demonstrating
genuine understanding? Boss levels must require novel reasoning — if
a boss level has an obvious template solution, flag it.

## How to report

For each item reviewed, write your assessment to:

  .codebase-mooc/memory/review_annotations/{component}_{layer}.json

Format:

{
  "reviewed_at": "<iso timestamp>",
  "reviewer": "curriculum-reviewer-skill",
  "flags": [
    {
      "severity": "error|warning|info",
      "failure_mode": "factual_accuracy|confabulation|pedagogy|exercise_quality",
      "message": "specific description of the issue",
      "location": "section or field where the issue appears"
    }
  ],
  "recommendation": "approve|regenerate|human_review",
  "notes": "any additional context for the human reviewer"
}

## When to approve

Approve content when it has no error-level flags. Warning-level flags
should be noted but do not block approval. Info-level flags are
observations for future improvement.

## When to require human review

Always require human review for:
- Any content in the decision_log layer with INFERRED decisions
- Any content in the failure_modes layer
- Any boss-level exercise
- Any content where you are uncertain about factual accuracy and
  cannot verify from the source code alone
