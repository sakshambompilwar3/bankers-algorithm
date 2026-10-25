"""
Matrix Tables & Dynamic Input Component
---------------------------------------
Provides scrollable, dynamically resizable, beautifully styled grid tables
for Total, Allocation, Maximum Demand, Need, and Available vectors.
Includes real-time cell change listeners to recompute Need and Available immediately.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable
from scenario_manager import ScenarioManager


class MatrixEditor(tk.Frame):
    """
    Scrollable matrix editor that displays:
    1. Total instances vector (editable)
    2. Allocation matrix (editable)
    3. Maximum Demand matrix (editable)
    4. Need matrix (live computed, read-only)
    5. Available vector (live computed, read-only)
    """

    def __init__(self, parent, scenario_mgr: ScenarioManager, on_change_callback: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(parent, bg="#F8FAFC", **kwargs)

        self.mgr = scenario_mgr
        self.on_change_callback = on_change_callback

        # References to entry widgets
        self.total_entries: List[tk.Entry] = []
        self.alloc_entries: List[List[tk.Entry]] = []
        self.max_entries: List[List[tk.Entry]] = []
        self.need_labels: List[List[tk.Label]] = []
        self.avail_labels: List[tk.Label] = []
        self.proc_name_entries: List[tk.Entry] = []
        self.res_name_entries: List[tk.Entry] = []

        self._build_ui()

    def _build_ui(self):
        # Create a scrollable canvas container so large matrices can scroll both horizontally and vertically
        self.canvas = tk.Canvas(self, bg="#F8FAFC", highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.scroll_content = tk.Frame(self.canvas, bg="#F8FAFC", padx=16, pady=16)
        self.scroll_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mouse wheel support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        # Support macOS smooth vertical wheel scrolling
        if self.canvas.winfo_exists():
            delta = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(delta, "units")

    def rebuild_tables(self):
        """Completely rebuilds the matrix grids based on current n and m."""
        for w in self.scroll_content.winfo_children():
            w.destroy()

        self.total_entries.clear()
        self.alloc_entries.clear()
        self.max_entries.clear()
        self.need_labels.clear()
        self.avail_labels.clear()
        self.proc_name_entries.clear()
        self.res_name_entries.clear()

        n = self.mgr.n
        m = self.mgr.m

        # -------------------------------------------------------------
        # Section 1: Resource Names & Total Instances + Available
        # -------------------------------------------------------------
        res_card = tk.LabelFrame(
            self.scroll_content, text=" System Resource Instances & Availability ",
            font=("Helvetica", 11, "bold"), fg="#0F172A", bg="#FFFFFF",
            padx=14, pady=12, highlightthickness=1, highlightbackground="#CBD5E1"
        )
        res_card.pack(fill=tk.X, pady=(0, 16))

        # Headers
        tk.Label(res_card, text="Resource Type:", font=("Helvetica", 10, "bold"), fg="#1E293B", bg="#FFFFFF", width=16, anchor="w").grid(row=0, column=0, padx=4, pady=4)
        tk.Label(res_card, text="Total Instances:", font=("Helvetica", 10, "bold"), fg="#0284C7", bg="#FFFFFF", width=16, anchor="w").grid(row=1, column=0, padx=4, pady=4)
        tk.Label(res_card, text="Initial Available:", font=("Helvetica", 10, "bold"), fg="#0369A1", bg="#FFFFFF", width=16, anchor="w").grid(row=2, column=0, padx=4, pady=4)

        for j in range(m):
            # Resource Name (editable)
            r_ent = tk.Entry(res_card, width=7, font=("Helvetica", 10, "bold"), justify="center", fg="#0F172A", bg="#F1F5F9")
            r_ent.insert(0, self.mgr.resource_names[j])
            r_ent.grid(row=0, column=j + 1, padx=4, pady=4)
            r_ent.bind("<FocusOut>", lambda e, col=j: self._on_res_name_changed(col))
            self.res_name_entries.append(r_ent)

            # Total entry (editable)
            t_val = self.mgr.total[j] if j < len(self.mgr.total) else 0
            t_ent = tk.Entry(res_card, width=7, font=("Helvetica", 10), justify="center", fg="#0284C7", bg="#FFFFFF")
            t_ent.insert(0, str(t_val))
            t_ent.grid(row=1, column=j + 1, padx=4, pady=4)
            t_ent.bind("<KeyRelease>", lambda e, col=j: self._on_total_cell_edit(col))
            self.total_entries.append(t_ent)

            # Available label (computed)
            avail_val = self.mgr.available[j] if j < len(self.mgr.available) else 0
            lbl_avail = tk.Label(
                res_card, text=str(avail_val), width=6, font=("Helvetica", 10, "bold"),
                fg="#0369A1", bg="#E0F2FE", relief=tk.SOLID, borderwidth=1
            )
            lbl_avail.grid(row=2, column=j + 1, padx=4, pady=4)
            self.avail_labels.append(lbl_avail)

        # -------------------------------------------------------------
        # Section 2: Allocation & Maximum Demand & Need Matrices
        # -------------------------------------------------------------
        matrices_frame = tk.Frame(self.scroll_content, bg="#F8FAFC")
        matrices_frame.pack(fill=tk.BOTH, expand=True)

        # Allocation Card
        alloc_card = tk.LabelFrame(
            matrices_frame, text=" Current Allocation Matrix ",
            font=("Helvetica", 11, "bold"), fg="#0F172A", bg="#FFFFFF",
            padx=12, pady=12, highlightthickness=1, highlightbackground="#CBD5E1"
        )
        alloc_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Max Demand Card
        max_card = tk.LabelFrame(
            matrices_frame, text=" Maximum Demand Matrix ",
            font=("Helvetica", 11, "bold"), fg="#0F172A", bg="#FFFFFF",
            padx=12, pady=12, highlightthickness=1, highlightbackground="#CBD5E1"
        )
        max_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        # Need Card (Computed preview)
        need_card = tk.LabelFrame(
            matrices_frame, text=" Need Matrix [Max - Alloc] ",
            font=("Helvetica", 11, "bold"), fg="#0F172A", bg="#FFFFFF",
            padx=12, pady=12, highlightthickness=1, highlightbackground="#CBD5E1"
        )
        need_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Build column headers for all 3 matrices
        for card, title_prefix in [(alloc_card, "Alloc"), (max_card, "Max"), (need_card, "Need")]:
            tk.Label(card, text="Process", font=("Helvetica", 10, "bold"), fg="#475569", bg="#FFFFFF", width=8, anchor="center").grid(row=0, column=0, padx=3, pady=3)
            for j in range(m):
                r_name = self.mgr.resource_names[j]
                tk.Label(card, text=r_name, font=("Helvetica", 10, "bold"), fg="#0284C7", bg="#FFFFFF", width=5, anchor="center").grid(row=0, column=j + 1, padx=3, pady=3)

        # Build rows for each process
        for i in range(n):
            p_name = self.mgr.process_names[i]

            # Allocation row
            p_ent = tk.Entry(alloc_card, width=8, font=("Helvetica", 10, "bold"), justify="center", fg="#0F172A", bg="#F1F5F9")
            p_ent.insert(0, p_name)
            p_ent.grid(row=i + 1, column=0, padx=3, pady=2)
            p_ent.bind("<FocusOut>", lambda e, row=i: self._on_proc_name_changed(row))
            self.proc_name_entries.append(p_ent)

            alloc_row_entries = []
            for j in range(m):
                val = self.mgr.allocation[i][j] if i < len(self.mgr.allocation) and j < len(self.mgr.allocation[i]) else 0
                ent = tk.Entry(alloc_card, width=5, font=("Helvetica", 10), justify="center", fg="#0F172A", bg="#FFFFFF")
                ent.insert(0, str(val))
                ent.grid(row=i + 1, column=j + 1, padx=3, pady=2)
                ent.bind("<KeyRelease>", lambda e, r=i, c=j: self._on_matrix_cell_edit("alloc", r, c))
                alloc_row_entries.append(ent)
            self.alloc_entries.append(alloc_row_entries)

            # Max Demand row
            tk.Label(max_card, text=p_name, font=("Helvetica", 10, "bold"), fg="#334155", bg="#F8FAFC", width=8, anchor="center").grid(row=i + 1, column=0, padx=3, pady=2)
            max_row_entries = []
            for j in range(m):
                val = self.mgr.maximum[i][j] if i < len(self.mgr.maximum) and j < len(self.mgr.maximum[i]) else 0
                ent = tk.Entry(max_card, width=5, font=("Helvetica", 10), justify="center", fg="#0F172A", bg="#FFFFFF")
                ent.insert(0, str(val))
                ent.grid(row=i + 1, column=j + 1, padx=3, pady=2)
                ent.bind("<KeyRelease>", lambda e, r=i, c=j: self._on_matrix_cell_edit("max", r, c))
                max_row_entries.append(ent)
            self.max_entries.append(max_row_entries)

            # Need row (computed labels)
            tk.Label(need_card, text=p_name, font=("Helvetica", 10, "bold"), fg="#334155", bg="#F8FAFC", width=8, anchor="center").grid(row=i + 1, column=0, padx=3, pady=2)
            need_row_labels = []
            for j in range(m):
                need_val = self.mgr.need[i][j] if i < len(self.mgr.need) and j < len(self.mgr.need[i]) else 0
                lbl_need = tk.Label(
                    need_card, text=str(need_val), width=5, font=("Helvetica", 10),
                    fg="#0F172A", bg="#F1F5F9", relief=tk.SOLID, borderwidth=1
                )
                lbl_need.grid(row=i + 1, column=j + 1, padx=3, pady=2)
                need_row_labels.append(lbl_need)
            self.need_labels.append(need_row_labels)

    def _on_total_cell_edit(self, col: int):
        val_str = self.total_entries[col].get().strip()
        try:
            val = int(val_str)
            if val >= 0:
                self.mgr.total[col] = val
                self._recalculate_live_previews()
        except ValueError:
            pass

    def _on_matrix_cell_edit(self, matrix_type: str, row: int, col: int):
        if matrix_type == "alloc":
            ent = self.alloc_entries[row][col]
        else:
            ent = self.max_entries[row][col]

        val_str = ent.get().strip()
        try:
            val = int(val_str)
            if val >= 0:
                if matrix_type == "alloc":
                    self.mgr.allocation[row][col] = val
                else:
                    self.mgr.maximum[row][col] = val
                self._recalculate_live_previews()
        except ValueError:
            pass

    def _on_proc_name_changed(self, row: int):
        new_name = self.proc_name_entries[row].get().strip()
        if new_name:
            self.mgr.process_names[row] = new_name
            self.mgr.mark_outdated()
            if self.on_change_callback:
                self.on_change_callback()

    def _on_res_name_changed(self, col: int):
        new_name = self.res_name_entries[col].get().strip()
        if new_name:
            self.mgr.resource_names[col] = new_name
            self.mgr.mark_outdated()
            if self.on_change_callback:
                self.on_change_callback()

    def _recalculate_live_previews(self):
        """Recomputes Need and Available live and updates UI labels without losing focus."""
        self.mgr.mark_outdated()

        # Update Available labels
        for j in range(self.mgr.m):
            if j < len(self.mgr.available) and j < len(self.avail_labels):
                avail_val = self.mgr.available[j]
                color = "#0369A1" if avail_val >= 0 else "#BE123C"
                self.avail_labels[j].config(text=str(avail_val), fg=color)

        # Update Need labels
        for i in range(self.mgr.n):
            for j in range(self.mgr.m):
                if i < len(self.mgr.need) and j < len(self.mgr.need[i]):
                    if i < len(self.need_labels) and j < len(self.need_labels[i]):
                        need_val = self.mgr.need[i][j]
                        color = "#0F172A" if need_val >= 0 else "#BE123C"
                        self.need_labels[i][j].config(text=str(need_val), fg=color)

        if self.on_change_callback:
            self.on_change_callback()

    def highlight_process_row(self, proc_idx: int, bg_color: str = "#DBEAFE"):
        """Highlights a specific process row across matrices during simulation."""
        for i in range(self.mgr.n):
            is_active = (i == proc_idx)
            row_bg = bg_color if is_active else "#FFFFFF"
            need_bg = "#BAE6FD" if is_active else "#F1F5F9"

            if i < len(self.alloc_entries):
                for ent in self.alloc_entries[i]:
                    ent.config(bg=row_bg)
            if i < len(self.max_entries):
                for ent in self.max_entries[i]:
                    ent.config(bg=row_bg)
            if i < len(self.need_labels):
                for lbl in self.need_labels[i]:
                    lbl.config(bg=need_bg)
