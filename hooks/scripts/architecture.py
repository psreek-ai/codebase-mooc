#!/usr/bin/env python3
"""
architecture.py — PreToolUse / Write|Edit|MultiEdit hook

Fires before file writes. Detects architectural signals in the content
being written and pre-signals the coordinator that a structural change
is incoming. This gives the coordinator early context before the commit
hook fires.

Must always exit 0 and output {"continue": true}.
Must never block or slow down the write operation.
"""

import json
import sys
from pathlib import Path


# Patterns that indicate an architectural change is in progress
ARCHITECTURAL_SIGNALS = [
    "class ",
    "def ",
    "interface ",
    "type ",
    "struct ",
    "enum ",
    "export default",
    "export class",
    "export function",
    "@app.route",
    "@router.",
    "app.get(",
    "app.post(",
    "app.put(",
    "app.delete(",
    "@Controller",
    "@Service",
    "@Repository",
    "func main()",
    "fn main()",
]

SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".java", ".go", ".rs", ".rb", ".cs",
    ".kt", ".swift", ".scala",
}


def find_project_root() -> Path | None:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".codebase-mooc" / "config.json").exists():
            return parent
    return None


def is_architecturally_significant(file_path: str, content: str) -> bool:
    path = Path(file_path)

    # Only source files
    if path.suffix.lower() not in SOURCE_EXTENSIONS:
        return False

    # Count architectural signals in the content
    hits = sum(1 for signal in ARCHITECTURAL_SIGNALS if signal in content)
    return hits >= 2


def main() -> None:
    output = {"continue": True}

    try:
        raw = sys.stdin.read().strip()
        if not raw:
            print(json.dumps(output))
            return

        hook_input = json.loads(raw)
        tool_name = hook_input.get("tool_name", "")

        if tool_name not in ("Write", "Edit", "MultiEdit"):
            print(json.dumps(output))
            return

        tool_input = hook_input.get("tool_input", {})
        file_path = tool_input.get("path", "")
        content = tool_input.get("content", tool_input.get("new_str", ""))

        if not is_architecturally_significant(file_path, content):
            print(json.dumps(output))
            return

        root = find_project_root()
        if not root:
            print(json.dumps(output))
            return

        memory = root / ".codebase-mooc" / "memory"
        memory.mkdir(parents=True, exist_ok=True)

        # Write a low-priority pre-signal to the queue.
        # The significance hook will write a higher-priority event
        # after the commit. This just gives the coordinator early notice.
        with open(memory / "coordinator_queue.jsonl", "a") as f:
            f.write(
                json.dumps({
                    "event_type":   "pre_write_architectural_signal",
                    "workflow":     "incremental_update",
                    "priority":     "low",
                    "file_path":    file_path,
                    "triggered_by": "architecture_hook",
                })
                + "\n"
            )

    except Exception:
        pass  # Never crash. Never block the write.

    print(json.dumps(output))


if __name__ == "__main__":
    main()
