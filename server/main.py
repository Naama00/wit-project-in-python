"""
ChartGenerator – produces all CodeGuard analysis charts as PNG files.

Design decisions:
* `matplotlib.use("Agg")` must be set *before* pyplot is imported so charts
  render correctly on a headless server (no display).
* Each chart method is independent; failures in one do not block the others.
* All paths returned are relative strings suitable for building URL links.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")   # noqa: E402  must come before pyplot import

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import List, Optional

from server.models import FileAnalysisResult
from server.history_store import HistoryStore, PushRecord

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRAPHS_DIR = Path("graphs")

# Colour palette – consistent across all charts
_PALETTE = {
    "blue":   "#4C72B0",
    "orange": "#DD8452",
    "green":  "#55A868",
    "red":    "#C44E52",
    "purple": "#8172B3",
    "grey":   "#8C8C8C",
}
_THRESHOLD_COLOR = "#C44E52"
_FIGURE_DPI = 150
_TITLE_FONT = {"fontsize": 14, "fontweight": "bold", "pad": 12}


# ---------------------------------------------------------------------------
# ChartGenerator
# ---------------------------------------------------------------------------

class ChartGenerator:
    """
    Generates all four analysis charts and returns a list of relative file paths.

    Args:
        history_store: Injected :class:`HistoryStore` instance used by the
                       line chart.  Pass *None* to skip that chart.
    """

    def __init__(self, history_store: Optional[HistoryStore] = None) -> None:
        self._history_store = history_store

    def generate_all(self, results: List[FileAnalysisResult]) -> List[str]:
        """
        Generates every chart that has enough data to render.

        Returns a list of server-relative paths (e.g. ``"graphs/histogram.png"``).
        """
        GRAPHS_DIR.mkdir(exist_ok=True)

        generators = [
            self._histogram_function_lengths,
            self._pie_chart_issue_types,
            self._bar_chart_issues_per_file,
            self._line_chart_issues_over_time,
        ]

        saved_paths: List[str] = []
        for generator in generators:
            try:
                path = generator(results)
                if path:
                    saved_paths.append(str(path))
            except Exception:
                # A failing chart must never break the analysis response.
                pass

        return saved_paths

    # ------------------------------------------------------------------
    # Chart 1 – Histogram: distribution of function lengths
    # ------------------------------------------------------------------

    def _histogram_function_lengths(
        self, results: List[FileAnalysisResult]
    ) -> Optional[Path]:
        all_lengths = [length for r in results for length in r.function_lengths]
        if not all_lengths:
            return None

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(
            all_lengths,
            bins=max(1, min(20, len(all_lengths))),
            color=_PALETTE["blue"],
            edgecolor="white",
            linewidth=0.6,
        )
        ax.axvline(
            x=20,
            color=_THRESHOLD_COLOR,
            linestyle="--",
            linewidth=1.5,
            label=f"Max allowed ({20} lines)",
        )
        ax.set_title("Distribution of Function Lengths", **_TITLE_FONT)
        ax.set_xlabel("Lines of Code per Function", labelpad=8)
        ax.set_ylabel("Number of Functions", labelpad=8)
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        path = GRAPHS_DIR / "histogram_function_lengths.png"
        fig.savefig(path, dpi=_FIGURE_DPI)
        plt.close(fig)
        return path

    # ------------------------------------------------------------------
    # Chart 2 – Pie chart: proportion of issue types
    # ------------------------------------------------------------------

    def _pie_chart_issue_types(
        self, results: List[FileAnalysisResult]
    ) -> Optional[Path]:
        issue_counts: dict[str, int] = {}
        for file_result in results:
            for issue in file_result.issues:
                issue_counts[issue.issue_type] = (
                    issue_counts.get(issue.issue_type, 0) + 1
                )

        if not issue_counts:
            return None

        labels = list(issue_counts.keys())
        sizes = list(issue_counts.values())
        colours = list(_PALETTE.values())[: len(labels)]

        fig, ax = plt.subplots(figsize=(8, 6))
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            autopct="%1.1f%%",
            colors=colours,
            startangle=140,
            wedgeprops={"linewidth": 0.8, "edgecolor": "white"},
        )
        for autotext in autotexts:
            autotext.set_fontsize(10)

        ax.legend(
            wedges,
            [f"{lbl} ({cnt})" for lbl, cnt in zip(labels, sizes)],
            loc="lower center",
            bbox_to_anchor=(0.5, -0.12),
            ncol=2,
            frameon=False,
            fontsize=9,
        )
        ax.set_title("Issues by Type", **_TITLE_FONT)
        fig.tight_layout()

        path = GRAPHS_DIR / "pie_chart_issue_types.png"
        fig.savefig(path, dpi=_FIGURE_DPI, bbox_inches="tight")
        plt.close(fig)
        return path

    # ------------------------------------------------------------------
    # Chart 3 – Bar chart: number of issues per file
    # ------------------------------------------------------------------

    def _bar_chart_issues_per_file(
        self, results: List[FileAnalysisResult]
    ) -> Optional[Path]:
        if not results:
            return None

        filenames = [r.filename for r in results]
        issue_counts = [len(r.issues) for r in results]
        bar_colours = [
            _PALETTE["red"] if count > 0 else _PALETTE["green"]
            for count in issue_counts
        ]

        fig, ax = plt.subplots(figsize=(max(8, len(filenames) * 1.5), 5))
        bars = ax.bar(filenames, issue_counts, color=bar_colours, edgecolor="white")

        # Annotate each bar with its value
        for bar, count in zip(bars, issue_counts):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                str(count),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_title("Number of Issues per File", **_TITLE_FONT)
        ax.set_xlabel("File", labelpad=8)
        ax.set_ylabel("Issue Count", labelpad=8)
        ax.set_ylim(0, max(issue_counts, default=1) + 1)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.xticks(rotation=20, ha="right")

        legend_patches = [
            mpatches.Patch(color=_PALETTE["red"], label="Has issues"),
            mpatches.Patch(color=_PALETTE["green"], label="No issues"),
        ]
        ax.legend(handles=legend_patches, frameon=False)

        fig.tight_layout()
        path = GRAPHS_DIR / "bar_chart_issues_per_file.png"
        fig.savefig(path, dpi=_FIGURE_DPI)
        plt.close(fig)
        return path

    # ------------------------------------------------------------------
    # Chart 4 (BONUS) – Line chart: issues over time
    # ------------------------------------------------------------------

    def _line_chart_issues_over_time(
        self, results: List[FileAnalysisResult]
    ) -> Optional[Path]:
        if self._history_store is None:
            return None

        records: List[PushRecord] = self._history_store.all_records()
        if len(records) < 2:
            return None

        timestamps = [r.timestamp for r in records]
        totals = [r.total_issues for r in records]

        # Shorten x-axis labels to HH:MM on the same day, else date
        short_labels = []
        for ts in timestamps:
            try:
                short_labels.append(ts[5:16].replace("T", " "))  # MM-DD HH:MM
            except IndexError:
                short_labels.append(ts)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(short_labels, totals, marker="o", color=_PALETTE["purple"], linewidth=2)
        ax.fill_between(
            range(len(totals)), totals, alpha=0.15, color=_PALETTE["purple"]
        )

        ax.set_title("Total Issues Over Time (per push)", **_TITLE_FONT)
        ax.set_xlabel("Push timestamp", labelpad=8)
        ax.set_ylabel("Total Issues", labelpad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.xticks(rotation=25, ha="right", fontsize=8)
        fig.tight_layout()

        path = GRAPHS_DIR / "line_chart_issues_over_time.png"
        fig.savefig(path, dpi=_FIGURE_DPI)
        plt.close(fig)
        return path
