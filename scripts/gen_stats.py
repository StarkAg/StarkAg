#!/usr/bin/env python3
"""
Generate stats.svg: contributions in the last year, active days, best week,
and a sparkline — in the same dark/minimal style as the reference profile
this was inspired by. No third-party stat-card service; drawn from the real
GraphQL contribution calendar, so it can't rate-limit or go dark.

Run:
    GH_TOKEN=<token> python3 scripts/gen_stats.py

Writes stats.svg next to this script's parent (repo root). Safe to run
repeatedly — output is deterministic for the same underlying data.
"""
import json
import os
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
USERNAME = os.environ.get("GH_USERNAME", "StarkAg")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN (a GitHub token with no special scopes needed "
                 "for public data) before running this script.")
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={USERNAME}"],
        capture_output=True, text=True, env={**os.environ, "GH_TOKEN": token},
    )
    if result.returncode != 0:
        sys.exit(f"gh api graphql failed:\n{result.stderr}")
    return json.loads(result.stdout)


def compute(data):
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]

    all_days = [d for w in weeks for d in w["contributionDays"]]
    active_days = sum(1 for d in all_days if d["contributionCount"] > 0)

    week_totals = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    best_week = max(week_totals) if week_totals else 0

    return dict(total=total, active_days=active_days, best_week=best_week,
                week_totals=week_totals)


def sparkline_path(values, width, height, pad=2):
    if not values or max(values) == 0:
        return "", ""
    n = len(values)
    vmax = max(values)
    xs = [pad + i * (width - 2 * pad) / max(n - 1, 1) for i in range(n)]
    ys = [height - pad - (v / vmax) * (height - 2 * pad) for v in values]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = line + f" L{xs[-1]:.1f},{height - pad:.1f} L{xs[0]:.1f},{height - pad:.1f} Z"
    return line, area


def render(stats):
    W, H = 620, 200
    line, area = sparkline_path(stats["week_totals"], width=W - 40, height=70)

    svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .bg {{ fill: #0d1117; }}
    .num {{ font: 700 40px 'JetBrains Mono', 'SF Mono', Menlo, monospace; fill: #f0f6fc; }}
    .lbl {{ font: 400 13px 'JetBrains Mono', 'SF Mono', Menlo, monospace; fill: #8b949e; }}
    .small-num {{ font: 700 22px 'JetBrains Mono', 'SF Mono', Menlo, monospace; fill: #f0f6fc; }}
  </style>
  <rect class="bg" width="{W}" height="{H}" rx="8"/>

  <text x="24" y="56" class="num">{stats['total']:,}</text>
  <text x="24" y="80" class="lbl">contributions in the last year</text>

  <text x="{W - 24}" y="34" text-anchor="end" class="small-num">{stats['active_days']}</text>
  <text x="{W - 24}" y="52" text-anchor="end" class="lbl">active days</text>
  <text x="{W - 24}" y="80" text-anchor="end" class="small-num">{stats['best_week']}</text>
  <text x="{W - 24}" y="98" text-anchor="end" class="lbl">best week</text>

  <g transform="translate(20, 108)">
    <path d="{area}" fill="#238636" fill-opacity="0.25"/>
    <path d="{line}" fill="none" stroke="#3fb950" stroke-width="1.5"/>
  </g>
</svg>
"""
    return svg


if __name__ == "__main__":
    stats = compute(fetch())
    svg = render(stats)
    out = ROOT / "stats.svg"
    changed = not out.exists() or out.read_text() != svg
    out.write_text(svg)
    print(f"total={stats['total']} active_days={stats['active_days']} "
          f"best_week={stats['best_week']}")
    print(f"{'wrote' if changed else 'unchanged'}: {out}")
