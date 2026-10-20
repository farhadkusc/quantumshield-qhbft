#!/usr/bin/env python3
"""Write docs/figures/results.svg from the n=64 rows of evaluation.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    report = json.loads((ROOT / "benchmarks" / "results" / "evaluation.json").read_text())
    rows = [r for r in report["rows"] if r["n"] == 64]
    labels = [f"{r['protocol']}\n{r['scheme']}" for r in rows]
    values = [r["bytes"] / 1e6 for r in rows]
    width, height = 720, 340
    left, bottom, plot_w, plot_h = 56, 78, 640, 200
    ymax = max(values) * 1.15
    colors = ["#8d6e63", "#1f4e79", "#1f4e79", "#5b8c5a", "#6b4c9a", "#c47b3a"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="56" y="28" font-family="Georgia, serif" font-size="16" fill="#1a1a1a">Bytes per decision at n = 64</text>',
    ]
    for tick in (0, 10, 20, 30, 40):
        y = bottom + plot_h - (tick / ymax) * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        parts.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#444">{tick}</text>'
        )
    bar_w = 64
    gap = (plot_w - len(rows) * bar_w) / (len(rows) + 1)
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        h = (value / ymax) * plot_h
        x = left + gap + i * (bar_w + gap)
        y = bottom + plot_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}"/>')
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#222">{value:.2f}</text>'
        )
        line1, line2 = label.split("\n")
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{bottom + plot_h + 18}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#222">{line1}</text>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{bottom + plot_h + 34}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#444">{line2}</text>'
        )
    parts.append("</svg>")
    out = ROOT / "docs" / "figures" / "results.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n")
    print(out)


if __name__ == "__main__":
    main()
