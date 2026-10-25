"""
Resource Request Testing Panel
------------------------------
Allows the user to select any process, input an arbitrary resource request vector,
and tests the request against Banker's Algorithm rules:
1. Request <= Need
2. Request <= Available
3. Tentative allocation safety check
Includes full rollback guarantee and optional apply-to-scenario button.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable
from scenario_manager import ScenarioManager
from banker_algorithm import RequestResult


class RequestTester(tk.Frame):
    """Interactive Resource Request simulation and evaluation panel."""

    def __init__(self, parent, scenario_mgr: ScenarioManager, on_apply_callback: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(parent, bg="#F8FAFC", **kwargs)

        self.mgr = scenario_mgr
        self.on_apply_callback = on_apply_callback
        self.request_entries: List[tk.Entry] = []
        self.last_result: Optional[RequestResult] = None

        self._build_ui()

    def _build_ui(self):
        # Top Container
        top_frame = tk.Frame(self, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1", padx=16, pady=14)
        top_frame.pack(fill=tk.X, padx=16, pady=(16, 12))

        tk.Label(
            top_frame, text="Simulate a New Process Resource Request",
            font=("Helvetica", 13, "bold"), fg="#0F172A", bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            top_frame,
            text="Test whether granting an immediate request from a process is safe according to Banker's Algorithm.\n"
                 "Denied requests are automatically rolled back without altering the current scenario.",
            font=("Helvetica", 10), fg="#475569", bg="#FFFFFF", justify=tk.LEFT
        ).pack(anchor="w", pady=(0, 12))

        # Inputs Grid
        input_grid = tk.Frame(top_frame, bg="#F1F5F9", padx=14, pady=12, highlightthickness=1, highlightbackground="#E2E8F0")
        input_grid.pack(fill=tk.X)

        tk.Label(input_grid, text="Select Requesting Process:", font=("Helvetica", 10, "bold"), fg="#1E293B", bg="#F1F5F9").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)

        self.proc_var = tk.StringVar()
        self.proc_combo = ttk.Combobox(input_grid, textvariable=self.proc_var, state="readonly", width=12)
        self.proc_combo.grid(row=0, column=1, sticky="w", pady=6)
        self.proc_combo.bind("<<ComboboxSelected>>", lambda e: self._on_proc_selected())

        # Current Need preview for selected process
        self.lbl_selected_need = tk.Label(
            input_grid, text="Declared Need: —",
            font=("Helvetica", 10), fg="#0284C7", bg="#F1F5F9"
        )
        self.lbl_selected_need.grid(row=0, column=2, sticky="w", padx=(16, 0), pady=6)

        # Dynamic Request Vector Entries Container
        self.req_entries_frame = tk.Frame(input_grid, bg="#F1F5F9")
        self.req_entries_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 6))

        # Buttons row
        btn_row = tk.Frame(top_frame, bg="#FFFFFF")
        btn_row.pack(fill=tk.X, pady=(12, 0))

        self.btn_test = tk.Button(
            btn_row, text="🔍 Evaluate Resource Request", command=self.evaluate_request,
            font=("Helvetica", 11, "bold"), fg="#FFFFFF", bg="#2563EB",
            activebackground="#1D4ED8", activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=14, pady=6, cursor="hand2"
        )
        self.btn_test.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_apply = tk.Button(
            btn_row, text="✔ Apply to Current Scenario", command=self.apply_request,
            font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#0284C7",
            activebackground="#0369A1", activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2", state=tk.DISABLED
        )
        self.btn_apply.pack(side=tk.LEFT, padx=4)

        # Decision & Staged Evaluation Result
        self.result_container = tk.Frame(self, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1", padx=16, pady=14)
        self.result_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        self.lbl_decision_banner = tk.Label(
            self.result_container, text="Awaiting Request Evaluation...",
            font=("Helvetica", 12, "bold"), fg="#475569", bg="#F1F5F9",
            padx=12, pady=10, relief=tk.SOLID, borderwidth=1, anchor="w"
        )
        self.lbl_decision_banner.pack(fill=tk.X, pady=(0, 12))

        # 3 Stages Inspection Card
        stages_box = tk.Frame(self.result_container, bg="#FFFFFF")
        stages_box.pack(fill=tk.X, pady=(0, 12))

        self.lbl_stage1 = tk.Label(
            stages_box, text="Phase 1: Request ≤ Need Check — Pending",
            font=("Helvetica", 10), fg="#334155", bg="#F8FAFC", padx=8, pady=6, anchor="w",
            relief=tk.SOLID, borderwidth=1
        )
        self.lbl_stage1.pack(fill=tk.X, pady=3)

        self.lbl_stage2 = tk.Label(
            stages_box, text="Phase 2: Request ≤ Available Check — Pending",
            font=("Helvetica", 10), fg="#334155", bg="#F8FAFC", padx=8, pady=6, anchor="w",
            relief=tk.SOLID, borderwidth=1
        )
        self.lbl_stage2.pack(fill=tk.X, pady=3)

        self.lbl_stage3 = tk.Label(
            stages_box, text="Phase 3: Tentative State Safety Check — Pending",
            font=("Helvetica", 10), fg="#334155", bg="#F8FAFC", padx=8, pady=6, anchor="w",
            relief=tk.SOLID, borderwidth=1
        )
        self.lbl_stage3.pack(fill=tk.X, pady=3)

        # Detailed Explanation Textbox
        tk.Label(
            self.result_container, text="Analysis & Rollback Details:",
            font=("Helvetica", 10, "bold"), fg="#0F172A", bg="#FFFFFF"
        ).pack(anchor="w", pady=(8, 4))

        self.txt_details = tk.Text(
            self.result_container, height=6, font=("Menlo", 10),
            bg="#F8FAFC", fg="#0F172A", highlightthickness=1,
            highlightbackground="#CBD5E1", relief=tk.FLAT, padx=10, pady=8
        )
        self.txt_details.pack(fill=tk.BOTH, expand=True)

    def refresh_scenario(self):
        """Updates process combo and resource vector fields to match current scenario."""
        self.proc_combo['values'] = self.mgr.process_names
        if self.mgr.process_names:
            if self.proc_var.get() not in self.mgr.process_names:
                self.proc_combo.current(0)
            self._on_proc_selected()

        # Rebuild resource entries
        for w in self.req_entries_frame.winfo_children():
            w.destroy()
        self.request_entries.clear()

        tk.Label(
            self.req_entries_frame, text="Requested Vector:",
            font=("Helvetica", 10, "bold"), fg="#1E293B", bg="#F1F5F9"
        ).pack(side=tk.LEFT, padx=(0, 10))

        for j, res_name in enumerate(self.mgr.resource_names):
            box = tk.Frame(self.req_entries_frame, bg="#F1F5F9")
            box.pack(side=tk.LEFT, padx=4)

            tk.Label(box, text=res_name, font=("Helvetica", 9, "bold"), fg="#0284C7", bg="#F1F5F9").pack()
            ent = tk.Entry(box, width=5, justify="center", font=("Helvetica", 10))
            ent.insert(0, "0")
            ent.pack()
            self.request_entries.append(ent)

        self.btn_apply.config(state=tk.DISABLED)
        self.lbl_decision_banner.config(
            text="Awaiting Request Evaluation...", bg="#F1F5F9", fg="#475569"
        )
        self.lbl_stage1.config(text="Phase 1: Request ≤ Need Check — Pending", bg="#F8FAFC", fg="#334155")
        self.lbl_stage2.config(text="Phase 2: Request ≤ Available Check — Pending", bg="#F8FAFC", fg="#334155")
        self.lbl_stage3.config(text="Phase 3: Tentative State Safety Check — Pending", bg="#F8FAFC", fg="#334155")
        self.txt_details.delete("1.0", tk.END)

    def _on_proc_selected(self):
        try:
            idx = self.mgr.process_names.index(self.proc_var.get())
            need_vec = self.mgr.need[idx] if idx < len(self.mgr.need) else []
            self.lbl_selected_need.config(text=f"Declared Need: {need_vec}")
        except Exception:
            self.lbl_selected_need.config(text="Declared Need: —")

    def evaluate_request(self):
        """Reads user input vector and runs request simulation."""
        if not self.proc_var.get() or self.proc_var.get() not in self.mgr.process_names:
            messagebox.showwarning("Selection Required", "Please select a valid process from the list.")
            return

        p_idx = self.mgr.process_names.index(self.proc_var.get())

        req_vector = []
        for j, ent in enumerate(self.request_entries):
            val_str = ent.get().strip()
            try:
                val = int(val_str)
                if val < 0:
                    raise ValueError()
                req_vector.append(val)
            except ValueError:
                res_name = self.mgr.resource_names[j]
                messagebox.showerror("Invalid Input", f"Request for resource '{res_name}' must be a non-negative integer.")
                return

        if all(v == 0 for v in req_vector):
            messagebox.showwarning("Zero Request", "Please specify at least 1 resource unit to request.")
            return

        res = self.mgr.execute_request_simulation(p_idx, req_vector)
        self.last_result = res
        self._display_result(res)

    def _display_result(self, res: RequestResult):
        self.txt_details.delete("1.0", tk.END)

        # Phase 1
        if res.rejection_stage == 1:
            self.lbl_stage1.config(text=f"✖ Phase 1 FAILED: {res.rejection_reason}", bg="#FFE4E6", fg="#BE123C")
            self.lbl_stage2.config(text="Phase 2: Skipped", bg="#F8FAFC", fg="#94A3B8")
            self.lbl_stage3.config(text="Phase 3: Skipped", bg="#F8FAFC", fg="#94A3B8")
        else:
            self.lbl_stage1.config(
                text=f"✔ Phase 1 PASSED: Request {res.request_vector} ≤ Remaining Need {res.original_need[res.process_index]}",
                bg="#E0F2FE", fg="#0369A1"
            )

        # Phase 2
        if res.rejection_stage == 2:
            self.lbl_stage2.config(text=f"✖ Phase 2 FAILED: {res.rejection_reason}", bg="#FFE4E6", fg="#BE123C")
            self.lbl_stage3.config(text="Phase 3: Skipped", bg="#F8FAFC", fg="#94A3B8")
        elif res.rejection_stage is None or res.rejection_stage == 3:
            self.lbl_stage2.config(
                text=f"✔ Phase 2 PASSED: Request {res.request_vector} ≤ Currently Available {res.original_available}",
                bg="#E0F2FE", fg="#0369A1"
            )

        # Phase 3
        if res.rejection_stage == 3:
            self.lbl_stage3.config(
                text=f"✖ Phase 3 FAILED: Tentative allocation results in an UNSAFE STATE (Deadlock risk detected).",
                bg="#FFE4E6", fg="#BE123C"
            )
        elif res.is_granted:
            safe_seq = " → ".join(res.safety_result.safe_sequence) if res.safety_result else ""
            self.lbl_stage3.config(
                text=f"✔ Phase 3 PASSED: Tentative state is SAFE. Safe Sequence found: < {safe_seq} >",
                bg="#E0F2FE", fg="#0369A1"
            )

        # Overall Banner
        if res.is_granted:
            self.lbl_decision_banner.config(
                text=f"✔ REQUEST APPROVED & CAN BE SAFELY GRANTED TO {res.process_name}!",
                bg="#E0F2FE", fg="#0369A1"
            )
            self.btn_apply.config(state=tk.NORMAL)
        else:
            self.lbl_decision_banner.config(
                text=f"✖ REQUEST DENIED FOR {res.process_name} — ALL CHANGES ROLLED BACK!",
                bg="#FFE4E6", fg="#BE123C"
            )
            self.btn_apply.config(state=tk.DISABLED)

        # Details
        log_text = f"Simulating Request: Process {res.process_name} requesting vector {res.request_vector}\n"
        log_text += f"• Original Available:  {res.original_available}\n"
        log_text += f"• Original Allocation: {res.original_allocation[res.process_index]}\n"
        log_text += f"• Original Need:       {res.original_need[res.process_index]}\n"
        log_text += "\nTentative State (if allocated):\n"
        log_text += f"• Tentative Available:  {res.tentative_available}\n"
        log_text += f"• Tentative Allocation: {res.tentative_allocation[res.process_index]}\n"
        log_text += f"• Tentative Need:       {res.tentative_need[res.process_index]}\n\n"
        log_text += f"Algorithm Verdict:\n{res.explanation}\n"

        self.txt_details.insert(tk.END, log_text)

    def apply_request(self):
        """Commits granted request to active scenario."""
        if self.last_result and self.last_result.is_granted:
            confirmed = messagebox.askyesno(
                "Apply Request",
                f"Are you sure you want to officially apply request {self.last_result.request_vector} "
                f"for process {self.last_result.process_name} to the active scenario?"
            )
            if confirmed:
                self.mgr.apply_granted_request()
                if self.on_apply_callback:
                    self.on_apply_callback()
                messagebox.showinfo("Success", f"Request successfully granted and committed to {self.last_result.process_name}!")
