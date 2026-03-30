---
name: codebase-archaeologist
description: |
  Use when working in a project with Codebase Memory available and
  the task requires understanding system architecture, component
  relationships, design decisions, or where code belongs.
  Activates automatically when debugging unfamiliar code, explaining
  system behaviour, tracing data flows, or reasoning about where a
  change should live.
  Trigger phrases: "how does X work", "where does Y live",
  "explain this code", "what calls this", "where should I put",
  "walk me through", "what is this doing".
version: 1.0.0
allowed-tools: Read
---

# Codebase Archaeologist

When this skill activates, use the Read tool to read Codebase Memory at:

  .codebase-mooc/memory/codebase/graph.json

Find the components relevant to the current task. For each relevant
component surface:
- Its purpose and core responsibilities
- Its interfaces — what it exposes and what it consumes
- Its relationships to other components
- The design decisions that shaped it
- Known failure modes
- What a developer must understand before modifying it

Ground every explanation in the actual system architecture, not
general reasoning about how systems like this typically work.

If .codebase-mooc/memory/codebase/graph.json does not exist in this
project, tell the developer that running /codebase-mooc:generate will
build it, then answer from general reasoning as best you can.

If the graph exists but the relevant component is not in it, note the
gap and suggest running /codebase-mooc:generate to rebuild with the
latest codebase.
