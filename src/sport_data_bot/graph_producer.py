"""Matplotlib charts for BetFair market probability output."""

from __future__ import annotations

import math
import os

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm


class GraphProducer:
    """Renders barplot and piechart figures styled for Discord embeds."""

    def __init__(self) -> None:
        """Load fonts and the red→blue gradient used for bar colouring."""
        self.colours = [
            "#0400ff",
            "#0600fc",
            "#0900f9",
            "#0b00f7",
            "#0e00f4",
            "#1000f2",
            "#1300ef",
            "#1500ec",
            "#1800ea",
            "#1a00e7",
            "#1d00e5",
            "#1f00e2",
            "#2200e0",
            "#2400dd",
            "#2700da",
            "#2a00d8",
            "#2c00d5",
            "#2f00d3",
            "#3100d0",
            "#3400ce",
            "#3600cb",
            "#3900c8",
            "#3b00c6",
            "#3e00c3",
            "#4000c1",
            "#4300be",
            "#4500bc",
            "#4800b9",
            "#4a00b6",
            "#4d00b4",
            "#5000b1",
            "#5200af",
            "#5500ac",
            "#5700aa",
            "#5a00a7",
            "#5c00a4",
            "#5f00a2",
            "#61009f",
            "#64009d",
            "#66009a",
            "#690097",
            "#6b0095",
            "#6e0092",
            "#710090",
            "#73008d",
            "#76008b",
            "#780088",
            "#7b0085",
            "#7d0083",
            "#800080",
            "#82007e",
            "#85007b",
            "#870079",
            "#8a0076",
            "#8c0073",
            "#8f0071",
            "#91006e",
            "#94006c",
            "#970069",
            "#990067",
            "#9c0064",
            "#9e0061",
            "#a1005f",
            "#a3005c",
            "#a6005a",
            "#a80057",
            "#ab0054",
            "#ad0052",
            "#b0004f",
            "#b2004d",
            "#b5004a",
            "#b80048",
            "#ba0045",
            "#bd0042",
            "#bf0040",
            "#c2003d",
            "#c4003b",
            "#c70038",
            "#c90036",
            "#cc0033",
            "#ce0030",
            "#d1002e",
            "#d3002b",
            "#d60029",
            "#d80026",
            "#db0024",
            "#de0021",
            "#e0001e",
            "#e3001c",
            "#e50019",
            "#e80017",
            "#ea0014",
            "#ed0012",
            "#ef000f",
            "#f2000c",
            "#f4000a",
            "#f70007",
            "#f90005",
            "#fc0002",
            "#ff0000",
        ]
        font_path = os.path.join(os.getcwd(), "sources", "Whitney Medium.ttf")
        self.large_font = fm.FontProperties(fname=font_path, size=16)
        self.medium_font = fm.FontProperties(fname=font_path, size=12)
        self.small_font = fm.FontProperties(fname=font_path, size=10)

    def preprocess_data(self, probabilities_dict: dict) -> tuple:
        """Collapse sub-1% entries into a 'Cumulative Other' bucket for display."""
        max_key = None
        removed_keys: list[str] = []
        cumulative_values = 0.0
        for key, value in probabilities_dict.items():
            if max_key is None or len(key) > len(max_key):
                max_key = key
            if value < 1.0:
                removed_keys.append(key)
                cumulative_values += value

        if cumulative_values != 0.0:
            [probabilities_dict.pop(key) for key in removed_keys]
            probabilities_dict["Cumulative Other (< 1%)"] = cumulative_values
            if max_key and len(max_key) < len("Cumulative Other (< 1%)"):
                max_key = "Cumulative Other (< 1%)"
        return max_key, probabilities_dict

    def barplot(self, event_name: str, market_name: str, datetime: str, probabilities_dict: dict):
        """Return a bar-chart figure for the given probabilities."""
        max_key, probabilities_dict = self.preprocess_data(probabilities_dict)

        barplot_colours = [self.colours[math.ceil(value) - 1] for value in probabilities_dict.values()]

        width = 8.4 if len(probabilities_dict) / 0.476 < 8.4 else len(probabilities_dict) / 0.476
        height = 8.4 if len(max_key) / 3.09 < 8.4 else len(max_key) / 3.09
        height += 5

        fig, ax = plt.subplots(figsize=(width, height))
        gs = gridspec.GridSpec(2, 1, width_ratios=[1], height_ratios=[height, height / 20])
        fig.clf()
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        ax1.patch.set_facecolor("#36393f")
        ax2.patch.set_facecolor("#36393f")

        plt.sca(ax1)
        plt.bar(probabilities_dict.keys(), probabilities_dict.values(), align="center", color=barplot_colours)
        plt.xticks(rotation=90, color="white", fontproperties=self.medium_font)
        plt.xlabel("\n" + event_name + " Runners\n\n", color="white", fontproperties=self.large_font)
        plt.yticks(np.arange(0, 101, step=5), fontsize=8, color="white", fontproperties=self.medium_font)
        plt.ylabel(market_name + " (%)", color="white", fontproperties=self.large_font)
        plt.text(
            0.99,
            0.99,
            "Source - Betfair.com API\nDate Processed (UTC) - {0}".format(datetime),
            fontproperties=self.small_font,
            color="white",
            horizontalalignment="right",
            verticalalignment="top",
            transform=ax1.transAxes,
        )
        plt.tight_layout()

        plt.sca(ax2)
        plt.bar([x for x in range(100)], [100 for _ in range(100)], align="center", width=1.0, color=self.colours)
        plt.box(False)
        x_ticks = ["" for _ in range(100)]
        x_ticks[0] = "0%"
        x_ticks[49] = "50%"
        x_ticks[99] = "100%"
        plt.tick_params(length=0)
        plt.xticks(np.arange(100), x_ticks, color="white", fontproperties=self.small_font)
        plt.yticks([])
        plt.tight_layout()

        return fig

    def piechart(self, event_name: str, market_name: str, datetime: str, probabilities_dict: dict):
        """Return a piechart figure for the given probabilities, or None if data is too sparse."""
        _max_key, probabilities_dict = self.preprocess_data(probabilities_dict)
        if sum(probabilities_dict.values()) < 90:
            return None

        fig, ax = plt.subplots(figsize=(12.8, 12.8))
        fig.clf()

        explode = [0.0 for _ in probabilities_dict.values()]
        explode[0] = 0.1
        plt.pie(
            probabilities_dict.values(),
            labels=probabilities_dict.keys(),
            shadow=True,
            explode=explode,
            textprops={"fontproperties": self.medium_font, "color": "white"},
        )
        plt.title("{0}\n{1}".format(event_name, market_name), color="white", fontproperties=self.large_font)
        return plt
