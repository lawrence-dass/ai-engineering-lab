"""Draws the article's charts from a committed run, with no model calls.

    uv run --with matplotlib python -m assets.make_charts --run main

Broken cases come from evals.report's own summarise() and compare(), so the
chart and report.md cannot disagree.
"""

import argparse
import re
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from evals.report import compare, load_rows, summarise  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# Display order: cheap models first, then strong, each vendor in the same slot order.
MODELS = [
    ("haiku", "Claude Haiku 5.5 (cheap)", "#2a78d6"),
    ("luna", "GPT-6 Luna (cheap)", "#eb6834"),
    ("opus", "Claude Opus 5.5 (strong)", "#1baf7a"),
    ("sol", "GPT-6.1 Sol (strong)", "#eda100"),
]
EDITS = [
    ("v2_keep_it_quick", "Keep it\nquick"),
    ("v3_add_example", "Add an\nexample"),
    ("v4_feel_heard", "Feel\nheard"),
    ("v5_tidy_urgency", "Tidy the\nurgency rule"),
    ("v6_bundled_pr", "Three changes\nat once"),
]
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"


def by_model_version(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["version"])].append(row)
    return grouped


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(TEXT_2)
    ax.tick_params(colors=TEXT_2, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def grouped_bars(ax, values: dict[str, list[float]], labels: list[str], fmt) -> None:
    n = len(MODELS)
    width = 0.8 / n
    gap = 0.02  # surface gap between adjacent bars
    for i, (key, name, color) in enumerate(MODELS):
        xs = [g + (i - (n - 1) / 2) * width for g in range(len(labels))]
        bars = ax.bar(xs, values[key], width - gap, color=color, label=name, edgecolor=SURFACE, linewidth=1)
        for bar, value in zip(bars, values[key]):
            ax.annotate(fmt(value), (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                        fontsize=9, color=TEXT)
    ax.set_xticks(range(len(labels)), labels, color=TEXT, fontsize=10)


def broken_chart(grouped, out: Path) -> None:
    values = {}
    for key, _, _ in MODELS:
        base = summarise(grouped[(key, "v1_baseline")])
        values[key] = [len(compare(base, summarise(grouped[(key, v)]))["broken"]) for v, _ in EDITS]
    fig, ax = plt.subplots(figsize=(9, 5), dpi=200, facecolor=SURFACE)
    style(ax)
    grouped_bars(ax, values, [label for _, label in EDITS], lambda v: f"{v:d}")
    ax.set_ylabel("Cases broken (of 50)", color=TEXT_2)
    ax.set_ylim(0, max(max(v) for v in values.values()) + 1.5)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    fig.suptitle("The tidy-up broke 6 or 7 cases on cheap models, 0 or 1 on strong ones",
                 x=0.06, ha="left", fontsize=13.5, color=TEXT, fontweight="bold")
    ax.set_title("Cases that passed every try on the baseline and failed most tries after the edit. "
                 "3 tries per case.", loc="left", fontsize=9.5, color=TEXT_2)
    ax.legend(frameon=False, fontsize=9, labelcolor=TEXT, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def cost_chart(grouped, out: Path) -> None:
    versions = [("v1_baseline", "Baseline"), ("v5_tidy_urgency", "Tidy the\nurgency rule"),
                ("v6_bundled_pr", "Three changes\nat once")]
    fig, axes = plt.subplots(1, 2, figsize=(9, 5), dpi=200, facecolor=SURFACE)
    for ax, keys in zip(axes, (("haiku", "luna"), ("opus", "sol"))):
        style(ax)
        n = len(keys)
        width = 0.8 / n
        for i, key in enumerate(keys):
            name, color = next((m[1], m[2]) for m in MODELS if m[0] == key)
            ys = []
            for v, _ in versions:
                rows = grouped[(key, v)]
                ys.append(1000 * sum(r["cost_usd"] for r in rows) / len(rows))
            xs = [g + (i - (n - 1) / 2) * width for g in range(len(versions))]
            bars = ax.bar(xs, ys, width - 0.02, color=color, label=name, edgecolor=SURFACE, linewidth=1)
            for bar, y in zip(bars, ys):
                ax.annotate(f"${y:.2f}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.5, color=TEXT)
        ax.set_xticks(range(len(versions)), [label for _, label in versions], color=TEXT, fontsize=9.5)
        ax.set_ylabel("Cost per 1,000 calls (USD)", color=TEXT_2)
        ax.legend(frameon=False, fontsize=8.5, labelcolor=TEXT, loc="upper left")
        ax.set_ylim(0, ax.get_ylim()[1] * 1.2)
    fig.suptitle("A shorter prompt lost OpenAI's cache and cost about 3 times as much",
                 x=0.06, ha="left", fontsize=13, color=TEXT, fontweight="bold")
    fig.text(0.06, 0.855, "The tidy-up cut the prompt to about 1,024 tokens on OpenAI, its cache minimum, so most calls missed the cache.\n"
             "Claude caches from 512 tokens and was unaffected. Cheap models left, strong right.", fontsize=9, color=TEXT_2)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def model_info(key: str) -> tuple[str, str]:
    return next((name, color) for k, name, color in MODELS if k == key)


def pass_rate_chart(grouped, out: Path) -> None:
    """Pass rate with its 95% interval per edit, and the broken-case count beside it."""
    versions = [("v1_baseline", "Base-\nline")] + EDITS
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), dpi=200, facecolor=SURFACE, sharey=True)
    all_overlap = True
    for ax, (key, name, color) in zip(axes.flat, MODELS):
        style(ax)
        base = summarise(grouped[(key, "v1_baseline")])
        for x, (v, _) in enumerate(versions):
            summary = summarise(grouped[(key, v)])
            low, high = summary["ci"]
            if v != "v1_baseline" and (low > base["ci"][1] or high < base["ci"][0]):
                all_overlap = False
            ax.plot([x, x], [100 * low, 100 * high], color=color, linewidth=2, solid_capstyle="round")
            ax.plot(x, 100 * summary["pass_rate"], "o", markersize=8, color=color,
                    markeredgecolor=SURFACE, markeredgewidth=2)
            if v != "v1_baseline":
                broken = len(compare(base, summary)["broken"])
                ax.annotate(f"{broken} broken", (x, 100 * high), xytext=(0, 6), textcoords="offset points",
                            ha="center", fontsize=8.5, color=TEXT if broken else TEXT_2,
                            fontweight="bold" if broken else "normal")
        ax.axhspan(100 * base["ci"][0], 100 * base["ci"][1], color=GRID, alpha=0.6, zorder=0, linewidth=0)
        ax.set_title(name, loc="left", fontsize=10.5, color=TEXT)
        ax.set_xticks(range(len(versions)), [label for _, label in versions], fontsize=8, color=TEXT)
        ax.set_ylim(55, 104)
    for ax in axes[:, 0]:
        ax.set_ylabel("Pass rate (%)", color=TEXT_2)
    assert all_overlap, "the title claims every interval overlaps the baseline's"
    fig.suptitle("Every interval overlaps the baseline's. The case-by-case check still found the breaks",
                 x=0.05, ha="left", fontsize=13, color=TEXT, fontweight="bold")
    fig.text(0.05, 0.925, "Dot: pass rate over 50 cases. Line: 95% interval (bootstrap over cases). "
             "Grey band: the baseline's interval. Label: cases broken by the edit.", fontsize=9, color=TEXT_2)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def cost_scatter(grouped, out: Path) -> None:
    """Cost per 1,000 correct tickets against pass rate, on the baseline and on v5."""
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=200, facecolor=SURFACE)
    style(ax)
    ax.xaxis.grid(True, color=GRID, linewidth=1)
    per_correct = {}
    for key, name, color in MODELS:
        points = []
        for v in ("v1_baseline", "v5_tidy_urgency"):
            summary = summarise(grouped[(key, v)])
            points.append((1000 * summary["cost_per_correct"], 100 * summary["pass_rate"]))
        per_correct[key] = points[0][0]
        (bx, by), (vx, vy) = points
        ax.plot([bx, vx], [by, vy], color=color, linewidth=2, zorder=2)
        ax.plot(bx, by, "o", markersize=10, color=color, markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
        ax.plot(vx, vy, "o", markersize=13, markerfacecolor="none", markeredgecolor=color, markeredgewidth=2, zorder=4)
        below = key in ("sol", "opus")
        ax.annotate(f"{name.split(' (')[0]}\n${bx:.2f}", (bx, by), xytext=(0, -14 if below else 12),
                    textcoords="offset points", ha="center", va="top" if below else "bottom", fontsize=8.5, color=TEXT)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"${x:g}"))
    ax.tick_params(axis="x", colors=TEXT_2)
    ax.set_xlabel("Cost per 1,000 correct tickets (USD, log scale)", color=TEXT_2)
    ax.set_ylabel("Pass rate (%)", color=TEXT_2)
    ax.set_ylim(65, 98)
    ax.set_xlim(0.025, 6)
    ratio = per_correct["opus"] / per_correct["haiku"]
    fig.suptitle(f"Opus costs {ratio:.0f} times Haiku per correct ticket, for nearly the same baseline pass rate",
                 x=0.06, ha="left", fontsize=12.5, color=TEXT, fontweight="bold")
    fig.text(0.06, 0.865, "Filled dot: the baseline prompt. Open ring: after the urgency tidy-up (v5). Labels give the baseline cost.\n"
             "The cheap models lose accuracy. Sol keeps it, but its cost per correct ticket triples as the cache is lost.", fontsize=9, color=TEXT_2)
    fig.tight_layout(rect=(0, 0, 1, 0.85))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def read_predictions(path: Path) -> dict[str, dict[str, int]]:
    """Round 2 predicted broken cases, {model key: {version: n}}, from PREDICTIONS.md."""
    text = path.read_text().split("## Round 2", 1)[1].split("\n## ", 1)[0]
    columns = {"Haiku 5.5": "haiku", "Opus 5.5": "opus", "GPT-6 Luna": "luna", "GPT-6.1 Sol": "sol"}
    header = None
    predicted: dict[str, dict[str, int]] = defaultdict(dict)
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if "Edit" in cells:
            header = cells
            continue
        match = re.fullmatch(r"`(v\d_\w+)`", cells[0]) if header else None
        if match:
            for title, key in columns.items():
                predicted[key][match.group(1)] = int(cells[header.index(title)])
    assert all(len(v) == len(EDITS) for v in predicted.values()) and len(predicted) == 4
    return predicted


def predictions_chart(grouped, out: Path) -> None:
    predicted = read_predictions(ROOT / "PREDICTIONS.md")
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.8), dpi=200, facecolor=SURFACE, sharey=True)
    for ax, (key, name, color) in zip(axes, MODELS):
        style(ax)
        base = summarise(grouped[(key, "v1_baseline")])
        for y, (v, _) in enumerate(EDITS):
            actual = len(compare(base, summarise(grouped[(key, v)]))["broken"])
            guess = predicted[key][v]
            ax.plot([guess, actual], [y, y], color=GRID, linewidth=3, zorder=1, solid_capstyle="round")
            ax.plot(guess, y, "o", markersize=9, markerfacecolor=SURFACE, markeredgecolor=color, markeredgewidth=2, zorder=2)
            ax.plot(actual, y, "o", markersize=9, color=color, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, color=GRID, linewidth=1)
        ax.set_xlim(-0.6, 7.8)
        ax.set_xticks(range(0, 8, 2))
        ax.set_title(name.replace(" (", "\n("), loc="left", fontsize=9.5, color=TEXT)
        ax.set_xlabel("Cases broken", color=TEXT_2, fontsize=9)
    axes[0].set_yticks(range(len(EDITS)), [label.replace("\n", " ") for _, label in EDITS], fontsize=9, color=TEXT)
    axes[0].invert_yaxis()
    fig.suptitle("I expected \"feel heard\" and the three-change edit to do the damage. The tidy-up did",
                 x=0.04, ha="left", fontsize=12.5, color=TEXT, fontweight="bold")
    fig.text(0.04, 0.875, "Open dot: my prediction, committed before the run. Filled dot: what broke.",
             fontsize=9, color=TEXT_2)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="main")
    args = parser.parse_args()
    grouped = by_model_version(load_rows(ROOT / "runs" / args.run))
    broken_chart(grouped, HERE / "broken_by_edit.png")
    charts = {
        "broken_by_edit.png": broken_chart,
        "cost_per_call_cache.png": cost_chart,
        "pass_rate_vs_broken.png": pass_rate_chart,
        "cost_per_correct.png": cost_scatter,
        "predictions_vs_actual.png": predictions_chart,
    }
    for name, draw in charts.items():
        draw(grouped, HERE / name)
        print("wrote", HERE / name)


if __name__ == "__main__":
    main()
