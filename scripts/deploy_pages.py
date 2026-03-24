#!/usr/bin/env python3
"""Deploy _site/ to GitHub Pages via gh-pages branch.

Usage:
    python scripts/deploy_pages.py

Pushes the contents of _site/ to the gh-pages branch of origin.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    site_dir = Path("_site")
    if not site_dir.exists():
        print("Error: _site/ not found. Run build_static.py first.")
        sys.exit(1)

    # Get remote URL
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: No git remote 'origin' configured.")
        sys.exit(1)
    remote_url = result.stdout.strip()

    print(f"Deploying _site/ to {remote_url} (gh-pages branch)")

    # Clean any previous .git in _site
    git_dir = site_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)

    # Initialize a temporary git repo in _site and force-push to gh-pages
    subprocess.run(["git", "init"], cwd=site_dir, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=site_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Deploy static site to GitHub Pages"],
        cwd=site_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-f", remote_url, "HEAD:gh-pages"],
        cwd=site_dir,
        check=True,
    )

    # Clean up .git in _site (may fail on Windows due to file locks)
    try:
        shutil.rmtree(site_dir / ".git", ignore_errors=True)
    except Exception:
        pass

    print("\nDeployed successfully!")
    print("\nIf this is the first deploy, enable GitHub Pages:")
    print("  1. Go to repository Settings > Pages")
    print("  2. Source: 'Deploy from a branch'")
    print("  3. Branch: 'gh-pages', folder: '/ (root)'")
    print("  4. Click Save")
    print("  5. Site will be at: https://<user>.github.io/jobclass/")


if __name__ == "__main__":
    main()
