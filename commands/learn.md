---
description: Start or continue a learning session for a developer. Pass the developer's name or ID as the argument.
argument-hint: "<developer-name-or-id>"
allowed-tools: Read, Write
---

# /codebase-mooc:learn

$ARGUMENTS contains the learner ID or name.

If $ARGUMENTS is empty, ask: "Who is this learning session for?"
Use the response as the learner ID (lowercase, spaces to hyphens).

Check that .codebase-mooc/curriculum/architecture/overview.md
exists. If not, tell the developer to run /codebase-mooc:generate first
and stop.

Invoke the tutor agent with the learner ID in $ARGUMENTS.

The tutor handles everything from this point:
reading learner state, determining what to deliver, delivering content
or exercises, evaluating responses, and updating learner memory.
