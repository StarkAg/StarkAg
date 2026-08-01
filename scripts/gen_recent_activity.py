#!/usr/bin/env python3
"""
Rewrite the "Recent activity" block in README.md between the markers

    <!-- recent-activity:start -->
    <!-- recent-activity:end -->

with the 5 most recently pushed-to public, non-fork repos. Everything outside
those markers is left untouched.

Run:
    GH_TOKEN=<token> python3 scripts/gen_recent_activity.py
"""
import datetime
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
USERNAME = os.environ.get("GH_USERNAME", "StarkAg")
START = "<!-- recent-activity:start -->"
END = "<!-- recent-activity:end -->"


def fetch_repos():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN before running this script.")
    result = subprocess.run(
        ["gh", "api", f"users/{USERNAME}/repos?type=owner&sort=pushed&per_page=15"],
        capture_output=True, text=True, env={**os.environ, "GH_TOKEN": token},
    )
    if result.returncode != 0:
        sys.exit(f"gh api failed:\n{result.stderr}")
    return json.loads(result.stdout)


def relative_time(iso_ts):
    then = datetime.datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    days = (now - then).days
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 30:
        return f"{days // 7} week{'s' if days // 7 > 1 else ''} ago"
    return then.strftime("%b %Y")


def build_block(repos, limit=5):
    # Skip the profile repo itself and forks; keep the N most recently pushed.
    picked = [r for r in repos if not r["fork"] and r["name"] != USERNAME][:limit]
    lines = []
    for r in picked:
        desc = f" — {r['description']}" if r.get("description") else ""
        lines.append(f"- **[{r['name']}]({r['html_url']})**{desc}  "
                     f"<sub>{relative_time(r['pushed_at'])}</sub>")
    return "\n".join(lines)


def splice(readme_text, block):
    if START not in readme_text or END not in readme_text:
        sys.exit(f"README.md is missing {START} / {END} markers.")
    before, rest = readme_text.split(START, 1)
    _, after = rest.split(END, 1)
    return f"{before}{START}\n{block}\n{END}{after}"


if __name__ == "__main__":
    repos = fetch_repos()
    block = build_block(repos)
    readme_path = ROOT / "README.md"
    original = readme_path.read_text()
    updated = splice(original, block)
    changed = updated != original
    readme_path.write_text(updated)
    print(block)
    print(f"\n{'updated' if changed else 'unchanged'}: {readme_path}")
