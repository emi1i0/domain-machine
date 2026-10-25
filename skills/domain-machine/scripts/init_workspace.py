#!/usr/bin/env python3
"""
domain-machine: create the work folder for a run.

  domain-research/
    .gitignore        <- ignores everything except each run's report.md
    <slug>/           <- names lists, JSON results, analysis, report.html, report.md

The .gitignore lives inside domain-research/, so the project's own .gitignore is never touched.

Usage:
  init_workspace.py --slug acme                 # ./domain-research/acme/
  init_workspace.py --slug acme --root path/to/domain-research
"""

import argparse
import json
import re
import sys
from pathlib import Path

GITIGNORE = """\
# Created by domain-machine: only the final report.md of each run is versioned.
# Working files (names lists, JSON results, analysis, report.html) stay local.
*
!.gitignore
!*/
!*/report.md
"""


def ensure_gitignore(root):
    """Write root/.gitignore unless one already exists. Returns True if written."""
    gi = Path(root) / ".gitignore"
    if gi.exists():
        return False
    gi.parent.mkdir(parents=True, exist_ok=True)
    gi.write_text(GITIGNORE, encoding="utf-8")
    return True


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "project"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Create the domain-machine work folder.")
    ap.add_argument("--slug", required=True, help="project name; slugified")
    ap.add_argument("--root", default="domain-research", help="parent folder (default: ./domain-research)")
    args = ap.parse_args()
    root = Path(args.root)
    work = root / slugify(args.slug)
    work.mkdir(parents=True, exist_ok=True)
    wrote = ensure_gitignore(root)
    print(json.dumps({"workdir": str(work.resolve()), "gitignore": str((root / ".gitignore").resolve()),
                      "gitignore_created": wrote}, indent=2))


if __name__ == "__main__":
    main()
