#!/usr/bin/env python3
"""
significance.py — PostToolUse / Bash hook

Fires after every Bash tool call. Detects git commits. Classifies
the change using rule-based logic only — no model calls, no latency.
Significant changes are written to the coordinator queue and the
coordinator is spawned as a background process. Ambiguous changes
are written to classify_queue.jsonl for Claude Code to reason about
at the start of the next session.

Must always exit 0 and output {"continue": true}.
Must complete in under 500ms. Must never crash Claude Code.
"""

import json
import subprocess
import sys
from pathlib import Path


# Files that are never curriculum-relevant
SKIP_PATTERNS = {
    ".lock", "package-lock.json", "yarn.lock", "poetry.lock",
    "Pipfile.lock", "composer.lock", "Gemfile.lock",
    ".gitignore", ".gitattributes", "CHANGELOG", "CHANGELOG.md",
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    ".prettierrc", ".eslintrc", ".eslintrc.js", ".eslintrc.json",
    ".flake8", ".pylintrc", "mypy.ini", ".mypy.ini",
    "__pycache__", ".pyc", ".pyo",
    ".min.js", ".min.css", ".map",
    "thumbs.db", ".ds_store",
}

# Files that are almost always curriculum-relevant
SIGNIFICANT_PATTERNS = {
    "service", "model", "schema", "router", "controller",
    "handler", "middleware", "migration", "repository",
    "api", "auth", "database", "db", "core",
    "main", "app", "server", "client",
    "manager", "processor", "worker", "queue",
    "domain", "entity", "aggregate", "command", "event",
}


def find_project_root() -> Path | None:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".codebase-mooc" / "config.json").exists():
            return parent
    return None


def get_changed_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--name-only"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return [f for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        return []


def is_git_commit(tool_input: dict) -> bool:
    cmd = tool_input.get("command", "")
    return "git commit" in cmd or "git push" in cmd


def classify(files: list[str]) -> str:
    if not files:
        return "skip"

    # All files match skip patterns → definitely not significant
    if all(
        any(skip.lower() in f.lower() for skip in SKIP_PATTERNS)
        for f in files
    ):
        return "skip"

    # Any file matches significant patterns → significant
    if any(
        any(sig in f.lower() for sig in SIGNIFICANT_PATTERNS)
        for f in files
    ):
        return "significant"

    # Check file extensions — source files are at least worth queuing
    source_extensions = {
        ".py", ".ts", ".tsx", ".js", ".jsx",
        ".java", ".go", ".rs", ".rb", ".cs",
        ".kt", ".swift", ".scala", ".ex", ".exs",
        ".cpp", ".c", ".h", ".hpp",
    }
    if any(
        any(f.endswith(ext) for ext in source_extensions)
        for f in files
    ):
        return "ambiguous"

    return "skip"


def spawn_coordinator(root: Path) -> None:
    coordinator = root / ".codebase-mooc" / "scripts" / "coordinator.py"
    if coordinator.exists():
        subprocess.Popen(
            ["python3", str(coordinator), "--process-queue"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def main() -> None:
    output = {"continue": True}

    try:
        raw = sys.stdin.read().strip()
        if not raw:
            print(json.dumps(output))
            return

        hook_input = json.loads(raw)

        if hook_input.get("tool_name") != "Bash":
            print(json.dumps(output))
            return

        tool_input = hook_input.get("tool_input", {})
        if not is_git_commit(tool_input):
            print(json.dumps(output))
            return

        root = find_project_root()
        if not root:
            print(json.dumps(output))
            return

        files = get_changed_files()
        result = classify(files)
        memory = root / ".codebase-mooc" / "memory"
        memory.mkdir(parents=True, exist_ok=True)

        if result == "significant":
            with open(memory / "coordinator_queue.jsonl", "a") as f:
                f.write(
                    json.dumps({
                        "event_type":    "commit",
                        "workflow":      "incremental_update",
                        "priority":      "normal",
                        "changed_files": files,
                    })
                    + "\n"
                )
            spawn_coordinator(root)

        elif result == "ambiguous":
            with open(memory / "classify_queue.jsonl", "a") as f:
                f.write(
                    json.dumps({
                        "event_type":    "commit_needs_classification",
                        "changed_files": files,
                    })
                    + "\n"
                )

    except Exception:
        pass  # Never crash. Never block Claude Code.

    print(json.dumps(output))


if __name__ == "__main__":
    main()
