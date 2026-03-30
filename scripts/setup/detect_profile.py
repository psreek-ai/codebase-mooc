#!/usr/bin/env python3
"""
detect_profile.py

Auto-detects the codebase profile and writes .codebase-mooc/config.json.
Called by /codebase-mooc:init. Safe to re-run — updates existing config.

Usage:
    python3 detect_profile.py
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


SKIP_DIRS = {
    ".git", ".codebase-mooc", "node_modules", "__pycache__",
    ".venv", "venv", "env", "dist", "build", "target",
    ".next", ".nuxt", "vendor", ".tox", "coverage",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
}

LANGUAGE_MAP = {
    ".py":    "python",
    ".ts":    "typescript",
    ".tsx":   "typescript",
    ".js":    "javascript",
    ".jsx":   "javascript",
    ".java":  "java",
    ".go":    "go",
    ".rs":    "rust",
    ".rb":    "ruby",
    ".cs":    "csharp",
    ".cpp":   "cpp",
    ".c":     "c",
    ".kt":    "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".ex":    "elixir",
    ".exs":   "elixir",
}


def find_project_root() -> Path:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def count_extensions(root: Path) -> Counter:
    counts: Counter = Counter()
    try:
        for entry in root.rglob("*"):
            if any(skip in entry.parts for skip in SKIP_DIRS):
                continue
            if entry.is_file():
                counts[entry.suffix.lower()] += 1
    except PermissionError:
        pass
    return counts


def detect_language(ext_counts: Counter) -> str:
    lang_counts: Counter = Counter()
    for ext, count in ext_counts.items():
        lang = LANGUAGE_MAP.get(ext)
        if lang:
            lang_counts[lang] += count
    if not lang_counts:
        return "unknown"
    return lang_counts.most_common(1)[0][0]


def detect_framework(root: Path, language: str) -> str:
    if language == "python":
        if (root / "manage.py").exists():
            return "django"
        for f in ["requirements.txt", "pyproject.toml"]:
            try:
                content = (root / f).read_text().lower()
                for fw in ["fastapi", "flask", "django", "starlette", "tornado"]:
                    if fw in content:
                        return fw
            except FileNotFoundError:
                pass

    if language in ("typescript", "javascript"):
        try:
            pkg = json.loads((root / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:           return "nextjs"
            if "nuxt" in deps:           return "nuxt"
            if "@nestjs/core" in deps:   return "nestjs"
            if "react" in deps:          return "react"
            if "vue" in deps:            return "vue"
            if "svelte" in deps:         return "svelte"
            if "express" in deps:        return "express"
            if "fastify" in deps:        return "fastify"
            if "hono" in deps:           return "hono"
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

    if language in ("java", "kotlin"):
        try:
            pom = (root / "pom.xml").read_text().lower()
            if "spring"    in pom: return "spring"
            if "quarkus"   in pom: return "quarkus"
            if "micronaut" in pom: return "micronaut"
        except FileNotFoundError:
            pass

    if language == "go" and (root / "go.mod").exists():
        try:
            mod = (root / "go.mod").read_text().lower()
            if "gin-gonic" in mod: return "gin"
            if "echo"      in mod: return "echo"
            if "fiber"     in mod: return "fiber"
            if "chi"       in mod: return "chi"
        except FileNotFoundError:
            pass
        return "go-module"

    if language == "rust" and (root / "Cargo.toml").exists():
        try:
            cargo = (root / "Cargo.toml").read_text().lower()
            if "actix"  in cargo: return "actix"
            if "axum"   in cargo: return "axum"
            if "rocket" in cargo: return "rocket"
            if "warp"   in cargo: return "warp"
        except FileNotFoundError:
            pass
        return "cargo"

    return "unknown"


def detect_monorepo(root: Path) -> bool:
    signals = [
        (root / "lerna.json").exists(),
        (root / "pnpm-workspace.yaml").exists(),
        (root / "turbo.json").exists(),
        (root / "nx.json").exists(),
        (root / "rush.json").exists(),
        (root / "packages").is_dir() and (root / "package.json").exists(),
        (root / "services").is_dir() and (root / "package.json").exists(),
        (root / "apps").is_dir() and (root / "packages").is_dir(),
    ]
    return sum(signals) >= 2


def classify_size(total_files: int) -> str:
    if total_files < 200:   return "small"
    if total_files < 2000:  return "medium"
    if total_files < 20000: return "large"
    return "xlarge"


def detect_entry_points(root: Path, language: str) -> list[str]:
    patterns = {
        "python":     ["main.py", "app.py", "wsgi.py", "asgi.py", "manage.py"],
        "typescript": ["index.ts", "main.ts", "app.ts", "server.ts"],
        "javascript": ["index.js", "main.js", "app.js", "server.js"],
        "java":       ["Application.java", "Main.java", "App.java"],
        "go":         ["main.go", "cmd/main.go"],
        "rust":       ["src/main.rs", "src/lib.rs"],
    }
    found = []
    for pattern in patterns.get(language, []):
        matches = list(root.rglob(pattern))
        found.extend(str(m.relative_to(root)) for m in matches[:2])
    return found[:5]


def main() -> None:
    root = find_project_root()
    print(f"Detecting codebase profile in: {root}")

    ext_counts  = count_extensions(root)
    total_files = sum(ext_counts.values())
    language    = detect_language(ext_counts)
    framework   = detect_framework(root, language)
    is_monorepo = detect_monorepo(root)
    size        = classify_size(total_files)
    entry_points = detect_entry_points(root, language)

    print(f"  Language:    {language}")
    print(f"  Framework:   {framework}")
    print(f"  Monorepo:    {is_monorepo}")
    print(f"  Size:        {size} ({total_files} files)")

    config = {
        "version":      "1.0",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "language":     language,
        "framework":    framework,
        "is_monorepo":  is_monorepo,
        "size":         size,
        "total_files":  total_files,
        "entry_points": entry_points,
    }

    mooc_dir = root / ".codebase-mooc"
    mooc_dir.mkdir(parents=True, exist_ok=True)
    (mooc_dir / "config.json").write_text(json.dumps(config, indent=2))
    print(f"  Config written to .codebase-mooc/config.json")


if __name__ == "__main__":
    main()
