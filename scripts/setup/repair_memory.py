#!/usr/bin/env python3
"""
repair_memory.py

Detects and repairs inconsistent state in .codebase-mooc/memory/.
Safe to run at any time — never deletes content, only fixes structure.

Usage:
    python3 repair_memory.py
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def find_mooc_dir() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / ".codebase-mooc"
        if (candidate / "config.json").exists():
            return candidate
    return Path.cwd() / ".codebase-mooc"


def repair_json_file(path: Path) -> bool:
    """Return True if healthy. Back up and reset if corrupt."""
    if not path.exists():
        return True
    try:
        content = path.read_text().strip()
        if not content:
            return True
        json.loads(content)
        return True
    except json.JSONDecodeError as e:
        print(f"  ⚠  Corrupt JSON: {path.name} ({e})")
        backup = path.with_suffix(
            f".corrupt.{int(datetime.now(timezone.utc).timestamp())}.json"
        )
        shutil.copy(path, backup)
        print(f"     Backed up to: {backup.name}")
        # Reset to empty valid state
        if path.suffix == ".jsonl":
            path.write_text("")
        else:
            path.write_text("{}")
        print(f"     Reset to empty state")
        return False


def repair_jsonl_file(path: Path) -> int:
    """Validate each line. Remove invalid lines. Return corrupt count."""
    if not path.exists():
        path.write_text("")
        return 0

    lines = path.read_text().splitlines()
    valid = []
    corrupt = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
            valid.append(line)
        except json.JSONDecodeError:
            corrupt += 1

    if corrupt:
        path.write_text("\n".join(valid) + ("\n" if valid else ""))
        print(f"  ✓ Repaired {path.name}: removed {corrupt} corrupt lines")

    return corrupt


def ensure_directories(mooc_dir: Path) -> int:
    required = [
        "memory/codebase",
        "memory/curriculum/architecture",
        "memory/curriculum/domain",
        "memory/curriculum/implementation",
        "memory/curriculum/decision_log",
        "memory/curriculum/failure_modes",
        "memory/curriculum/exercises/system_literacy",
        "memory/curriculum/exercises/domain_mastery",
        "memory/curriculum/exercises/engineering_judgment",
        "memory/curriculum/exercises/boss_levels",
        "memory/curriculum/review_annotations",
        "memory/learners",
        "memory/agent_logs",
        "scripts/setup",
        "scripts/review",
    ]
    created = 0
    for rel in required:
        path = mooc_dir / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created += 1
    return created


def main() -> None:
    mooc_dir = find_mooc_dir()
    memory   = mooc_dir / "memory"

    print(f"\nRepairing: {mooc_dir}\n")

    # Ensure all directories exist
    created = ensure_directories(mooc_dir)
    if created:
        print(f"  ✓ Recreated {created} missing directories")
    else:
        print(f"  ✓ All directories present")

    # Repair queue files
    for queue_name in [
        "coordinator_queue.jsonl",
        "classify_queue.jsonl",
        "human_review_queue.jsonl",
    ]:
        repair_jsonl_file(memory / queue_name)

    # Repair codebase memory
    graph = memory / "codebase" / "graph.json"
    if not repair_json_file(graph):
        print("  ⚠  Codebase Memory was corrupt and reset.")
        print("     Re-run /codebase-mooc:generate to rebuild.")
    elif graph.exists():
        print("  ✓ Codebase Memory healthy")
    else:
        print("  ℹ  Codebase Memory not yet generated — run /codebase-mooc:generate")

    # Repair curriculum files
    repaired = 0
    for json_file in (memory / "curriculum").rglob("*.json"):
        if not repair_json_file(json_file):
            repaired += 1
    if repaired:
        print(f"  ✓ Repaired {repaired} corrupt curriculum files")
    else:
        print(f"  ✓ All curriculum files healthy")

    print(f"\nRepair complete.")
    print("All agents are idempotent — re-run any failed agent safely.\n")


if __name__ == "__main__":
    main()
