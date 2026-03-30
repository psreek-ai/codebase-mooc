#!/usr/bin/env python3
"""
coordinator.py

Reads the coordinator queue, determines workflows, and sequences
agent invocations. Does not generate curriculum content. Does not
make API calls. Sequences the agents that Claude Code runs.

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


def find_project_root() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".codebase-mooc" / "config.json").exists():
            return parent
    raise RuntimeError(
        ".codebase-mooc not found. Run /codebase-mooc:init first."
    )


class Coordinator:
    def __init__(self) -> None:
        self.root    = find_project_root()
        self.memory  = self.root / ".codebase-mooc" / "memory"
        self.scripts = self.root / ".codebase-mooc" / "scripts"
        self.queue   = self.memory / "coordinator_queue.jsonl"
        self.review  = self.memory / "human_review_queue.jsonl"

    # ── Queue processing ───────────────────────────────────────────────────

    def process_queue(self) -> int:
        if not self.queue.exists():
            return 0

        raw_lines = self.queue.read_text().splitlines()
        events = []
        for line in raw_lines:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        # Clear the queue before processing — prevents double-processing
        # if the coordinator is spawned again while running
        self.queue.write_text("")

        # Sort by priority
        priority_order = {"high": 0, "normal": 1, "low": 2}
        events.sort(key=lambda e: priority_order.get(e.get("priority", "normal"), 1))

        processed = 0
        for event in events:
            try:
                self._route(event)
                processed += 1
            except Exception as ex:
                print(f"  [coordinator] Error processing event: {ex}", file=sys.stderr)
                # Retry up to 3 times with increasing delay
                retry_count = event.get("retry_count", 0) + 1
                if retry_count < 3:
                    event["retry_count"] = retry_count
                    event["priority"] = "low"
                    self._enqueue(event)

        return processed

    # ── Routing ────────────────────────────────────────────────────────────

    def _route(self, event: dict) -> None:
        workflow = event.get("workflow", "incremental_update")

        dispatch = {
            "full_generation":    self._full_generation,
            "incremental_update": self._incremental_update,
            "pathologist_run":    self._pathologist_run,
            "regeneration":       self._regeneration,
        }

        handler = dispatch.get(workflow)
        if handler:
            handler(event)
        else:
            print(f"  [coordinator] Unknown workflow: {workflow}", file=sys.stderr)

    # ── Workflows ──────────────────────────────────────────────────────────

    def _full_generation(self, _event: dict) -> None:
        print("\n[coordinator] Full curriculum generation\n", flush=True)

        pipeline = [
            ("archaeologist", ["--full-run"]),
            ("architect",     ["--full-run"]),
            ("historian",     ["--full-run"]),
            ("instructor",    ["--full-run"]),
            ("pathologist",   ["--full-run"]),
            ("examiner",      ["--full-run"]),
            ("reviewer",      ["--full-run"]),
        ]

        for agent_name, args in pipeline:
            print(f"  → {agent_name}...", flush=True)
            success = self._run_agent(agent_name, args)
            if not success:
                print(f"  ✗ {agent_name} failed. Stopping pipeline.", file=sys.stderr)
                return

        # Queue all layers for human review
        self._queue_review(
            components=[],
            layers=[
                "architecture", "domain", "implementation",
                "decision_log", "failure_modes", "exercises",
            ],
            reason="Full generation — initial human review required",
        )

        print("\n[coordinator] Generation complete.", flush=True)
        print("  Run /codebase-mooc:review to process the review queue.", flush=True)

    def _incremental_update(self, event: dict) -> None:
        components = event.get("affected_components", [])
        comp_json  = json.dumps(components)

        self._run_agent("archaeologist", ["--affected-components", comp_json])
        self._run_agent("architect",     [])

        for comp in components:
            self._run_agent("historian",  ["--component", comp])
            self._run_agent("instructor", ["--component", comp])

        self._run_agent("reviewer", [])

        if components:
            self._queue_review(
                components=components,
                layers=["decision_log"],
                reason="Incremental update — decision log needs review",
            )

    def _pathologist_run(self, event: dict) -> None:
        incident_file = event.get("incident_file", "")
        self._run_agent("pathologist", ["--incident-file", incident_file])
        self._run_agent("reviewer",    [])
        self._queue_review(
            components=[],
            layers=["failure_modes"],
            reason=f"New incident: {incident_file}",
        )

    def _regeneration(self, event: dict) -> None:
        component = event.get("component", "")
        layer     = event.get("layer", "")
        feedback  = event.get("feedback", "")

        agent_map = {
            "architecture":   "architect",
            "domain":         "instructor",
            "implementation": "instructor",
            "decision_log":   "historian",
            "failure_modes":  "pathologist",
            "exercises":      "examiner",
        }

        agent_name = agent_map.get(layer)
        if not agent_name or not component:
            return

        args = ["--component", component]
        if feedback:
            args += ["--feedback", feedback]

        self._run_agent(agent_name, args)
        self._run_agent("reviewer",  [])
        self._queue_review(
            components=[component],
            layers=[layer],
            reason=f"Regenerated after rejection: {feedback}",
        )

    # ── Agent runner ───────────────────────────────────────────────────────

    def _run_agent(self, agent_name: str, args: list[str]) -> bool:
        """
        Runs the agent script as a subprocess.
        The agent script is a thin wrapper that prepares context
        and runs Claude Code in agent mode.
        """
        script = self.scripts / f"{agent_name}.py"
        if not script.exists():
            print(f"  [coordinator] Agent script not found: {script}", file=sys.stderr)
            return False

        result = subprocess.run(
            ["python3", str(script), *args],
            cwd=str(self.root),
        )
        return result.returncode == 0

    # ── Queue helpers ──────────────────────────────────────────────────────

    def _enqueue(self, event: dict) -> None:
        event["enqueued_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.queue, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _queue_review(
        self,
        components: list[str],
        layers: list[str],
        reason: str = "",
    ) -> None:
        self.review.parent.mkdir(parents=True, exist_ok=True)
        item = {
            "components": components,
            "layers":     layers,
            "reason":     reason,
            "status":     "pending",
            "queued_at":  datetime.now(timezone.utc).isoformat(),
        }
        with open(self.review, "a") as f:
            f.write(json.dumps(item) + "\n")


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Codebase MOOC Coordinator")
    parser.add_argument(
        "--process-queue",
        action="store_true",
        help="Process all pending events in the coordinator queue",
    )
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Trigger a full curriculum generation",
    )
    args = parser.parse_args()

    coordinator = Coordinator()

    if args.full_run:
        coordinator._full_generation({})
    elif args.process_queue:
        n = coordinator.process_queue()
        print(f"[coordinator] Processed {n} events")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
