"""
Resource Distribution Canvas Chart
-----------------------------------
A pure-Python Tkinter Canvas chart widget that displays:
- Per-resource Total, Allocated, and Available instances as clean grouped bars.
- Resource utilization percentage indicators.
- Crisp navy, blue, and light-blue styling.
- Responsive redrawing on container resize.
Requires ZERO external packages (no matplotlib required at runtime).
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional


class ResourceBarChart(tk.Frame):
    """Custom Tkinter Canvas chart displaying resource allocation breakdown."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#FFFFFF", **kwargs)

        self.resource_names: List[str] = []
        self.total: List[int] = []
        self.allocated: List[int] = []
        self.available: List[int] = []

        # Header info
        self.header_frame = tk.Frame(self, bg="#FFFFFF")
        self.header_frame.pack(fill=tk.X, padx=16, pady=(12, 6))

        self.title_lbl = tk.Label(
            self.header_frame,
            text="System Resource Utilization Chart",
            font=("Helvetica", 13, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        self.title_lbl.pack(side=tk.LEFT)

        # Legend
        self.legend_frame = tk.Frame(self.header_frame, bg="#FFFFFF")
        self.legend_frame.pack(side=tk.RIGHT)

        self._add_legend_item(self.legend_frame, "#0F172A", "Total Capacity")
        self._add_legend_item(self.legend_frame, "#2563EB", "Allocated")
        self._add_legend_item(self.legend_frame, "#38BDF8", "Available")

        # Canvas
        self.canvas = tk.Canvas(self, bg="#F8FAFC", highlightthickness=1, highlightbackground="#E2E8F0")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self.canvas.bind("<Configure>", lambda e: self.draw())

    def _add_legend_item(self, parent, color: str, label: str):
        item = tk.Frame(parent, bg="#FFFFFF")
        item.pack(side=tk.LEFT, padx=8)
        box = tk.Canvas(item, width=12, height=12, bg=color, highlightthickness=0)
        box.pack(side=tk.LEFT, padx=(0, 4))
        lbl = tk.Label(item, text=label, font=("Helvetica", 10), fg="#334155", bg="#FFFFFF")
        lbl.pack(side=tk.LEFT)

    def update_data(
        self,
        resource_names: List[str],
        total: List[int],
        allocation: List[List[int]],
        available: Optional[List[int]] = None
    ):
        """Updates chart data and redraws."""
        self.resource_names = list(resource_names)
        self.total = list(total)
        m = len(self.resource_names)

        # Calculate allocated sum per resource
        self.allocated = [0] * m
        for j in range(m):
            self.allocated[j] = sum(allocation[i][j] for i in range(len(allocation))) if allocation else 0

        if available is not None:
            self.available = list(available)
        else:
            self.available = [self.total[j] - self.allocated[j] for j in range(m)]

        self.draw()

    def draw(self):
        """Draws the bar chart onto the canvas."""
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100 or not self.resource_names:
            self.canvas.create_text(
                max(50, width // 2), max(50, height // 2),
                text="No resource data to display. Please configure or load a scenario.",
                font=("Helvetica", 11), fill="#64748B"
            )
            return

        margin_left = 60
        margin_right = 40
        margin_top = 40
        margin_bottom = 60

        plot_width = max(50, width - margin_left - margin_right)
        plot_height = max(50, height - margin_top - margin_bottom)

        max_val = max(max(self.total) if self.total else 1, 1)
        # Give 15% headroom
        y_max = max(10, int(max_val * 1.15) + 1)

        # Draw grid lines & Y-axis labels
        grid_steps = 5
        for i in range(grid_steps + 1):
            val = int(y_max * i / grid_steps)
            y = margin_top + plot_height - (val / y_max * plot_height)
            self.canvas.create_line(
                margin_left, y, margin_left + plot_width, y,
                fill="#E2E8F0", dash=(2, 2)
            )
            self.canvas.create_text(
                margin_left - 10, y,
                text=str(val), font=("Helvetica", 9), fill="#64748B", anchor="e"
            )

        # Axes lines
        self.canvas.create_line(
            margin_left, margin_top, margin_left, margin_top + plot_height,
            fill="#94A3B8", width=1.5
        )
        self.canvas.create_line(
            margin_left, margin_top + plot_height, margin_left + plot_width, margin_top + plot_height,
            fill="#94A3B8", width=1.5
        )

        m = len(self.resource_names)
        group_width = plot_width / m
        bar_width = min(28, max(12, int(group_width * 0.22)))
        spacing = 4

        for j in range(m):
            group_center = margin_left + (j + 0.5) * group_width
            r_name = self.resource_names[j]

            tot_val = self.total[j] if j < len(self.total) else 0
            alloc_val = self.allocated[j] if j < len(self.allocated) else 0
            avail_val = self.available[j] if j < len(self.available) else 0

            # 3 bars: Total, Allocated, Available
            bars = [
                (tot_val, "#0F172A", "Tot"),
                (alloc_val, "#2563EB", "Alc"),
                (avail_val, "#38BDF8", "Avail")
            ]

            start_x = group_center - (1.5 * bar_width + spacing)

            for idx, (val, color, lbl) in enumerate(bars):
                bx = start_x + idx * (bar_width + spacing)
                bar_h = (val / y_max) * plot_height if y_max > 0 else 0
                by1 = margin_top + plot_height - bar_h
                by2 = margin_top + plot_height

                # Bar rectangle
                self.canvas.create_rectangle(
                    bx, by1, bx + bar_width, by2,
                    fill=color, outline="#1E293B" if color == "#0F172A" else color,
                    width=1
                )

                # Value label on top of bar
                if bar_h > 14:
                    self.canvas.create_text(
                        bx + bar_width / 2, by1 - 8,
                        text=str(val), font=("Helvetica", 8, "bold"), fill="#1E293B"
                    )

            # Resource group label below X-axis
            util_pct = (alloc_val / tot_val * 100) if tot_val > 0 else 0
            self.canvas.create_text(
                group_center, margin_top + plot_height + 16,
                text=f"{r_name}", font=("Helvetica", 11, "bold"), fill="#0F172A"
            )
            self.canvas.create_text(
                group_center, margin_top + plot_height + 34,
                text=f"({util_pct:.0f}% used)", font=("Helvetica", 9), fill="#475569"
            )
