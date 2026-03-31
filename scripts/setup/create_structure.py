#!/usr/bin/env python3
"""
create_structure.py

Idempotent setup of all .codebase-mooc/ directories and baseline files.
Safe to re-run at any time — creates missing items, leaves existing ones.

Usage:
    python3 create_structure.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def find_project_root() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def create_structure(root: Path) -> int:
    mooc = root / ".codebase-mooc"

    directories = [
        # Internal JSON state (partially gitignored)
        mooc / "memory" / "codebase",
        mooc / "memory" / "review_annotations",
        mooc / "memory" / "learners",
        mooc / "memory" / "agent_logs",
        mooc / "scripts" / "setup",
        mooc / "scripts" / "review",
        # Human-readable Markdown curriculum (fully committed)
        mooc / "curriculum" / "architecture",
        mooc / "curriculum" / "domain",
        mooc / "curriculum" / "implementation",
        mooc / "curriculum" / "decision_log",
        mooc / "curriculum" / "failure_modes",
        mooc / "curriculum" / "exercises" / "system_literacy",
        mooc / "curriculum" / "exercises" / "domain_mastery",
        mooc / "curriculum" / "exercises" / "engineering_judgment",
        mooc / "curriculum" / "exercises" / "boss_levels",
    ]

    created = 0
    for d in directories:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created += 1

    # Memory .gitignore
    gitignore = mooc / "memory" / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# Personal learner data — stays local\n"
            "learners/\n"
            "agent_logs/\n"
            "coordinator_queue.jsonl\n"
            "classify_queue.jsonl\n"
            "human_review_queue.jsonl\n"
            "\n"
            "# Codebase memory and review annotations are committed\n"
            "!codebase/\n"
            "!review_annotations/\n"
        )

    # Empty queues
    for queue_name in [
        "coordinator_queue.jsonl",
        "classify_queue.jsonl",
        "human_review_queue.jsonl",
    ]:
        queue_path = mooc / "memory" / queue_name
        if not queue_path.exists():
            queue_path.write_text("")

    return created


def update_root_gitignore(root: Path) -> None:
    gitignore_path = root / ".gitignore"
    mooc_entries = [
        ".codebase-mooc/memory/learners/",
        ".codebase-mooc/memory/agent_logs/",
        ".codebase-mooc/memory/coordinator_queue.jsonl",
        ".codebase-mooc/memory/classify_queue.jsonl",
        ".codebase-mooc/memory/human_review_queue.jsonl",
    ]

    existing = gitignore_path.read_text() if gitignore_path.exists() else ""
    additions = [e for e in mooc_entries if e not in existing]

    if additions:
        with open(gitignore_path, "a") as f:
            f.write("\n# Codebase MOOC — personal data\n")
            for entry in additions:
                f.write(entry + "\n")


def main() -> None:
    root = find_project_root()
    print(f"Setting up .codebase-mooc/ in: {root}")

    created = create_structure(root)
    print(f"  Created {created} directories")

    update_root_gitignore(root)
    print("  Updated .gitignore")

    print("Done.")


if __name__ == "__main__":
    main()
