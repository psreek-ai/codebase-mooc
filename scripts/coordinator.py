#!/usr/bin/env python3
"""
coordinator.py

Routes events to agent workflows. Sequences agents. Does not generate
curriculum content. Does not make API calls.

Internal state files (queues, codebase memory, learner data) → JSON
Curriculum output (what developers read) → Markdown via agents

Directory layout:
  .codebase-mooc/memory/          ← JSON internal state (gitignored except graph + annotations)
  .codebase-mooc/curriculum/      ← Markdown curriculum (committed to git, human-readable)

Usage:
    python3 coordinator.py --process-queue
    python3 coordinator.py --full-run
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_root() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".codebase-mooc" / "config.json").exists():
            return parent
    raise RuntimeError(
        ".codebase-mooc not found. Run /codebase-mooc:init first."
    )


class Coordinator:
    def __init__(self) -> None:
        self.root    = find_root()
        self.mooc    = self.root / ".codebase-mooc"
        self.memory  = self.mooc / "memory"
        self.scripts = self.mooc / "scripts"
        self.queue   = self.memory / "coordinator_queue.jsonl"
        self.review  = self.memory / "human_review_queue.jsonl"

    def process_queue(self) -> int:
        if not self.queue.exists():
            return 0
        lines = self.queue.read_text().splitlines()
        events = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        self.queue.write_text("")

        events.sort(key=lambda e: {
            "high": 0, "normal": 1, "low": 2
        }.get(e.get("priority", "normal"), 1))

        processed = 0
        for event in events:
            try:
                self._route(event)
                processed += 1
            except Exception as ex:
                print(f"  [coordinator] Error: {ex}", file=sys.stderr)
                retry = event.get("retry_count", 0) + 1
                if retry < 3:
                    event["retry_count"] = retry
                    event["priority"] = "low"
                    self._enqueue(event)
        return processed

    def _route(self, event: dict) -> None:
        workflow = event.get("workflow", "incremental_update")
        {
            "full_generation":    self._full_generation,
            "incremental_update": self._incremental_update,
            "pathologist_run":    self._pathologist_run,
            "regeneration":       self._regeneration,
        }.get(workflow, self._incremental_update)(event)

    def _agent(self, name: str, *args) -> bool:
        """Invoke a Claude Code agent by name.

        Agents are defined as .md files in the plugin's agents/ directory.
        They are invoked via the `claude` CLI which loads the agent definition
        and runs it in a forked context.
        """
        agent_args = " ".join(args)
        prompt = f"Run the {name} agent with: {agent_args}" if agent_args else f"Run the {name} agent"
        try:
            result = subprocess.run(
                ["claude", "--print", "--agent", name, prompt],
                cwd=str(self.root),
                timeout=600,
            )
            return result.returncode == 0
        except FileNotFoundError:
            print(f"  ✗ 'claude' CLI not found. Install Claude Code to run agents.", file=sys.stderr)
            return False
        except subprocess.TimeoutExpired:
            print(f"  ✗ Agent {name} timed out after 10 minutes.", file=sys.stderr)
            return False

    def _full_generation(self, _event: dict) -> None:
        print("\n  Full curriculum generation\n", flush=True)
        pipeline = [
            ("archaeologist",   "--full-run"),  # → JSON codebase memory
            ("architect",       "--full-run"),  # → MD curriculum/architecture/
            ("domain-analyst",  "--full-run"),  # → MD curriculum/domain/
            ("historian",       "--full-run"),  # → MD curriculum/decision_log/
            ("instructor",      "--full-run"),  # → MD curriculum/implementation/
            ("pathologist",     "--full-run"),  # → MD curriculum/failure_modes/
            ("examiner",        "--full-run"),  # → MD curriculum/exercises/
            ("reviewer",        "--full-run"),  # → JSON review annotations
        ]
        for name, flag in pipeline:
            print(f"  → {name}...", flush=True)
            if not self._agent(name, flag):
                print(f"  ✗ {name} failed.", file=sys.stderr)
                return

        self._queue_review(
            [],
            ["architecture", "domain", "implementation", "decision_log",
             "failure_modes", "exercises"],
            "Full generation — initial human review required"
        )
        print("\n  Done. Run /codebase-mooc:review", flush=True)

    def _incremental_update(self, event: dict) -> None:
        comps = event.get("affected_components", [])
        cj    = json.dumps(comps)
        self._agent("archaeologist", "--affected-components", cj)
        self._agent("architect")
        for c in comps:
            self._agent("domain-analyst", "--component", c)
            self._agent("historian",      "--component", c)
            self._agent("instructor",     "--component", c)
        self._agent("reviewer")
        if comps:
            self._queue_review(comps, ["decision_log"],
                               "Incremental update")

    def _pathologist_run(self, event: dict) -> None:
        f = event.get("incident_file", "")
        self._agent("pathologist", "--incident-file", f)
        self._agent("reviewer")
        self._queue_review([], ["failure_modes"], f"New incident: {f}")

    def _regeneration(self, event: dict) -> None:
        c  = event.get("component", "")
        l  = event.get("layer", "")
        fb = event.get("feedback", "")
        agent = {
            "architecture":   "architect",
            "domain":         "domain-analyst",
            "implementation": "instructor",
            "decision_log":   "historian",
            "failure_modes":  "pathologist",
            "exercises":      "examiner",
        }.get(l)
        if agent and c:
            args = ["--component", c]
            if fb: args += ["--feedback", fb]
            self._agent(agent, *args)
            self._agent("reviewer")
            self._queue_review([c], [l], f"Regenerated: {fb}")

    def _enqueue(self, event: dict) -> None:
        event["enqueued_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.queue, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _queue_review(self, components: list, layers: list, reason: str = "") -> None:
        with open(self.review, "a") as f:
            f.write(json.dumps({
                "components": components,
                "layers":     layers,
                "reason":     reason,
                "status":     "pending",
                "queued_at":  datetime.now(timezone.utc).isoformat(),
            }) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-queue", action="store_true")
    parser.add_argument("--full-run",      action="store_true")
    args = parser.parse_args()
    c = Coordinator()
    if args.full_run:
        c._full_generation({})
    elif args.process_queue:
        print(f"[coordinator] Processed {c.process_queue()} events")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
