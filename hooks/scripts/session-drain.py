#!/usr/bin/env python3
"""
session-drain.py — Stop hook

Fires when a Claude Code session ends. Drains the coordinator queue
by spawning the coordinator as a background process. Also checks the
classify_queue for ambiguous commits that need Claude Code to reason
about them — these are logged for the next session.

Must always exit 0 and output {"continue": true}.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path | None:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".codebase-mooc" / "config.json").exists():
            return parent
    return None


def has_pending_items(queue_path: Path) -> bool:
    if not queue_path.exists():
        return False
    content = queue_path.read_text().strip()
    return bool(content)


def spawn_coordinator(root: Path) -> None:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if plugin_root:
        coordinator = Path(plugin_root) / "scripts" / "coordinator.py"
    else:
        coordinator = Path(__file__).resolve().parent.parent.parent / "scripts" / "coordinator.py"
    if coordinator.exists():
        subprocess.Popen(
            ["python3", str(coordinator), "--process-queue"],
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def promote_classify_queue(root: Path) -> None:
    """
    Move items from classify_queue into coordinator_queue as
    incremental_update events so the coordinator can handle them.
    The coordinator will ask Claude Code to classify them properly
    at the next session start.
    """
    memory = root / ".codebase-mooc" / "memory"
    classify_path = memory / "classify_queue.jsonl"

    if not classify_path.exists():
        return

    lines = classify_path.read_text().strip().splitlines()
    if not lines:
        return

    classify_path.write_text("")

    coordinator_queue = memory / "coordinator_queue.jsonl"
    with open(coordinator_queue, "a") as f:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                # Promote to a low-priority incremental update
                event = {
                    "event_type":    "commit",
                    "workflow":      "incremental_update",
                    "priority":      "low",
                    "changed_files": item.get("changed_files", []),
                    "source":        "classify_queue_promotion",
                }
                f.write(json.dumps(event) + "\n")
            except Exception:
                pass


def main() -> None:
    output = {"continue": True}

    try:
        root = find_project_root()
        if not root:
            print(json.dumps(output))
            return

        memory = root / ".codebase-mooc" / "memory"
        coordinator_queue = memory / "coordinator_queue.jsonl"
        classify_queue = memory / "classify_queue.jsonl"

        # Promote ambiguous commits from classify_queue
        promote_classify_queue(root)

        # Spawn coordinator if there is anything to process
        if has_pending_items(coordinator_queue):
            spawn_coordinator(root)

    except Exception:
        pass

    print(json.dumps(output))


if __name__ == "__main__":
    main()
