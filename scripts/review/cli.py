#!/usr/bin/env python3
"""
cli.py — Human Review CLI

Interactive CLI for processing the human review queue. Surfaces
Reviewer Agent flags alongside content so reviewers check targeted
concerns rather than reading cold.

Usage:
    python3 .codebase-mooc/scripts/review/cli.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_mooc_dir() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / ".codebase-mooc"
        if (candidate / "config.json").exists():
            return candidate
    return Path.cwd() / ".codebase-mooc"


def truncate(text: str, limit: int = 600) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n  ... [{len(text) - limit} more characters]"


def render_content(curriculum: dict) -> str:
    content = curriculum.get("content", curriculum)
    if isinstance(content, dict):
        return truncate(json.dumps(content, indent=2))
    return truncate(str(content))


def process_item(
    mooc_dir: Path,
    component: str,
    layer: str,
    reviewer_name: str,
) -> str:
    curriculum_path = (
        mooc_dir / "memory" / "curriculum" / layer / f"{component}.json"
    )
    annotation_path = (
        mooc_dir
        / "memory"
        / "curriculum"
        / "review_annotations"
        / f"{component}_{layer}.json"
    )

    if not curriculum_path.exists():
        print(f"  ⚠  Content not found: {layer}/{component} — skipping")
        return "skipped"

    try:
        curriculum  = json.loads(curriculum_path.read_text())
        annotations = (
            json.loads(annotation_path.read_text())
            if annotation_path.exists()
            else {}
        )
    except json.JSONDecodeError:
        print(f"  ⚠  Could not read files for {layer}/{component} — skipping")
        return "skipped"

    print(f"\n{'─' * 60}")
    print(f"  Layer:     {layer}")
    print(f"  Component: {component}")
    if curriculum.get("generated_at"):
        print(f"  Generated: {curriculum['generated_at'][:19]}")
    print(f"{'─' * 60}")

    # Reviewer Agent flags
    flags = annotations.get("flags", [])
    if flags:
        print("\n  Reviewer Agent flags:")
        for flag in flags:
            severity = flag.get("severity", "info")
            icons = {"error": "✗", "warning": "⚠", "info": "ℹ"}
            icon = icons.get(severity, "•")
            print(f"    {icon} [{severity.upper()}] {flag.get('message', str(flag))}")
        overall = annotations.get("overall_recommendation", "")
        if overall:
            print(f"\n  Reviewer recommendation: {overall.upper()}")
    else:
        print("\n  ✓ No flags from Reviewer Agent")

    # Decision log — show inferred count
    if layer == "decision_log":
        decisions = curriculum.get("decisions", [])
        inferred  = sum(1 for d in decisions if d.get("evidence_type") == "INFERRED")
        if inferred:
            print(
                f"\n  ℹ  {inferred} of {len(decisions)} decisions "
                f"are INFERRED (no direct git evidence)"
            )

    # Content preview
    print(f"\n  Content preview:\n")
    for line in render_content(curriculum).split("\n"):
        print(f"  {line}")

    # Decision
    print(f"\n  [a] Approve  [r] Reject with feedback  [s] Skip")
    try:
        choice = input("  Decision: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Interrupted — stopping review.")
        sys.exit(0)

    if choice == "a":
        curriculum["review_status"]  = "approved"
        curriculum["human_reviewer"] = reviewer_name
        curriculum["reviewed_at"]    = datetime.now(timezone.utc).isoformat()
        curriculum_path.write_text(json.dumps(curriculum, indent=2))
        print("  ✅ Approved")
        return "approved"

    elif choice == "r":
        try:
            reason = input("  Rejection reason: ").strip()
        except (EOFError, KeyboardInterrupt):
            reason = "No reason provided"

        curriculum["review_status"]    = "rejected"
        curriculum["rejection_reason"] = reason
        curriculum["human_reviewer"]   = reviewer_name
        curriculum["reviewed_at"]      = datetime.now(timezone.utc).isoformat()
        curriculum_path.write_text(json.dumps(curriculum, indent=2))

        # Queue for regeneration
        queue_path = find_mooc_dir() / "memory" / "coordinator_queue.jsonl"
        regen_event = {
            "event_type": "regeneration_requested",
            "workflow":   "regeneration",
            "component":  component,
            "layer":      layer,
            "feedback":   reason,
            "priority":   "normal",
        }
        with open(queue_path, "a") as f:
            f.write(json.dumps(regen_event) + "\n")

        print("  ❌ Rejected — queued for regeneration with your feedback")
        return "rejected"

    else:
        print("  ⏭  Skipped")
        return "skipped"


def main() -> None:
    mooc_dir    = find_mooc_dir()
    review_path = mooc_dir / "memory" / "human_review_queue.jsonl"

    print("\n" + "═" * 60)
    print("  Codebase MOOC — Human Review Queue")
    print("═" * 60 + "\n")

    if not review_path.exists() or not review_path.read_text().strip():
        print("  No items in review queue. 🎉\n")
        return

    all_items = []
    for line in review_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                all_items.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    pending = [i for i in all_items if i.get("status") == "pending"]

    if not pending:
        print("  No pending items. 🎉\n")
        return

    total = sum(
        max(len(item.get("components") or [""]), 1) * len(item.get("layers", []))
        for item in pending
    )
    print(f"  {total} item(s) pending review.\n")

    try:
        reviewer_name = input("  Your name (for audit trail): ").strip() or "anonymous"
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        return

    approved = rejected = skipped = 0

    for item in pending:
        components = item.get("components") or [""]
        layers     = item.get("layers", [])

        if item.get("reason"):
            print(f"\n  Reason: {item['reason']}")

        for component in components:
            for layer in layers:
                result = process_item(mooc_dir, component, layer, reviewer_name)
                if result == "approved":
                    approved += 1
                elif result == "rejected":
                    rejected += 1
                else:
                    skipped += 1

        item["status"]       = "processed"
        item["processed_at"] = datetime.now(timezone.utc).isoformat()
        item["reviewer"]     = reviewer_name

    # Rewrite queue with updated statuses
    review_path.write_text(
        "\n".join(json.dumps(i) for i in all_items) + "\n"
    )

    print(f"\n{'═' * 60}")
    print(f"  Review complete.")
    print(f"  Approved: {approved}  Rejected: {rejected}  Skipped: {skipped}")
    if rejected:
        print(f"  Rejected items queued for regeneration.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
