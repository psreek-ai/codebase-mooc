#!/usr/bin/env python3
"""
cli.py — Human Review CLI

Processes the human review queue. Reads Markdown curriculum files
alongside JSON review annotations so reviewers see both the
human-readable content and the specific flags from the Reviewer agent.

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


def find_curriculum_file(mooc_dir: Path, component: str, layer: str) -> Path | None:
    """
    Curriculum content is Markdown in .codebase-mooc/curriculum/
    Review annotations are JSON in .codebase-mooc/memory/review_annotations/
    """
    md_path = mooc_dir / "curriculum" / layer / f"{component}.md"
    if md_path.exists():
        return md_path

    # Boss levels and exercises use a different naming convention
    exercise_dir = mooc_dir / "curriculum" / "exercises"
    for arc_dir in exercise_dir.iterdir():
        if arc_dir.is_dir():
            for f in arc_dir.glob(f"{component}_*.md"):
                return f

    return None


def read_annotation(mooc_dir: Path, component: str, layer: str) -> dict:
    """Annotations are JSON — machine-written by the Reviewer agent."""
    path = mooc_dir / "memory" / "review_annotations" / f"{component}_{layer}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def truncate(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n  ... [{len(text) - limit} more chars — open the file to read in full]"


def process_item(
    mooc_dir: Path,
    component: str,
    layer: str,
    reviewer_name: str,
) -> str:
    md_path    = find_curriculum_file(mooc_dir, component, layer)
    annotation = read_annotation(mooc_dir, component, layer)

    if not md_path:
        print(f"  ⚠  Curriculum file not found: {layer}/{component} — skipping")
        return "skipped"

    try:
        md_content = md_path.read_text()
    except Exception:
        print(f"  ⚠  Could not read {md_path} — skipping")
        return "skipped"

    print(f"\n{'─' * 60}")
    print(f"  File:      {md_path.relative_to(mooc_dir.parent)}")
    print(f"  Layer:     {layer}")
    print(f"  Component: {component}")
    print(f"{'─' * 60}")

    # Show Reviewer agent flags (from JSON annotation)
    flags = annotation.get("flags", [])
    if flags:
        print("\n  Reviewer Agent flags:")
        for flag in flags:
            severity = flag.get("severity", "info")
            icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(severity, "•")
            print(f"    {icon} [{severity.upper()}] {flag.get('message', str(flag))}")
            if flag.get("location"):
                print(f"        Location: {flag['location']}")
        rec = annotation.get("overall_recommendation", "")
        if rec:
            print(f"\n  Reviewer recommendation: {rec.upper()}")
    else:
        print("\n  ✓ No flags from Reviewer Agent")

    # Show Markdown content preview
    print(f"\n  Content preview (Markdown):\n")
    for line in truncate(md_content).split("\n"):
        print(f"  {line}")
    print(f"\n  Full file: {md_path}")

    print(f"\n  [a] Approve  [r] Reject with feedback  [s] Skip")
    try:
        choice = input("  Decision: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Interrupted.")
        sys.exit(0)

    if choice == "a":
        # Update the Review status line in the Markdown frontmatter
        updated = md_content.replace(
            "Review status:** Pending",
            f"Review status:** Approved by {reviewer_name} · {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        )
        if updated == md_content:
            # Fallback: append approval note if frontmatter pattern not found
            updated = md_content + f"\n\n<!-- Approved by {reviewer_name} on {datetime.now(timezone.utc).date()} -->\n"
        md_path.write_text(updated)
        print("  ✅ Approved")
        return "approved"

    elif choice == "r":
        try:
            reason = input("  Rejection reason: ").strip()
        except (EOFError, KeyboardInterrupt):
            reason = "No reason provided"

        # Update review status in Markdown
        updated = md_content.replace(
            "Review status:** Pending",
            f"Review status:** Rejected — {reason}"
        )
        md_path.write_text(updated)

        # Queue for regeneration (coordinator queue is JSON)
        queue_path = mooc_dir / "memory" / "coordinator_queue.jsonl"
        with open(queue_path, "a") as f:
            f.write(json.dumps({
                "event_type": "regeneration_requested",
                "workflow":   "regeneration",
                "component":  component,
                "layer":      layer,
                "feedback":   reason,
                "priority":   "normal",
            }) + "\n")

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
        reviewer_name = input("  Your name: ").strip() or "anonymous"
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
                if result == "approved":   approved += 1
                elif result == "rejected": rejected += 1
                else:                      skipped  += 1
        item["status"]       = "processed"
        item["processed_at"] = datetime.now(timezone.utc).isoformat()
        item["reviewer"]     = reviewer_name

    review_path.write_text(
        "\n".join(json.dumps(i) for i in all_items) + "\n"
    )

    print(f"\n{'═' * 60}")
    print(f"  Approved: {approved}  Rejected: {rejected}  Skipped: {skipped}")
    if rejected:
        print("  Rejected items queued for regeneration.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
