"""
Simulation Stepper Component
----------------------------
Provides interactive step-by-step playback, live visualization of
Need <= Work evaluation, staged resource release animation, and safe sequence accumulation.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from banker_algorithm import SafetyResult, StepTrace


class SimulationStepper(tk.Frame):
    """Interactive step-by-step safety algorithm visualizer."""

    def __init__(self, parent, on_step_change: Optional[Callable[[int], None]] = None, **kwargs):
        super().__init__(parent, bg="#F8FAFC", **kwargs)

        self.on_step_change = on_step_change
        self.safety_result: Optional[SafetyResult] = None
        self.current_step_idx: int = -1  # -1 = initial state
        self.is_playing: bool = False
        self.timer_id: Optional[str] = None
        self.speed_ms: int = 1200

        self._build_ui()

    def _build_ui(self):
        # 1. Controls Bar
        ctrl_bar = tk.Frame(self, bg="#0F172A", padx=16, pady=10)
        ctrl_bar.pack(fill=tk.X)

        btn_style = {
            "font": ("Helvetica", 10, "bold"),
            "fg": "#FFFFFF",
            "bg": "#1E293B",
            "activebackground": "#334155",
            "activeforeground": "#FFFFFF",
            "relief": tk.FLAT,
            "padx": 10,
            "pady": 5,
            "cursor": "hand2"
        }

        self.btn_first = tk.Button(ctrl_bar, text="⏮ First", command=self.go_first, **btn_style)
        self.btn_first.pack(side=tk.LEFT, padx=3)

        self.btn_prev = tk.Button(ctrl_bar, text="◀ Prev", command=self.go_prev, **btn_style)
        self.btn_prev.pack(side=tk.LEFT, padx=3)

        self.btn_play = tk.Button(
            ctrl_bar, text="▶ Play", command=self.toggle_play,
            font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#0284C7",
            activebackground="#0369A1", activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=14, pady=5, cursor="hand2"
        )
        self.btn_play.pack(side=tk.LEFT, padx=6)

        self.btn_next = tk.Button(ctrl_bar, text="Next ▶", command=self.go_next, **btn_style)
        self.btn_next.pack(side=tk.LEFT, padx=3)

        self.btn_last = tk.Button(ctrl_bar, text="Last ⏭", command=self.go_last, **btn_style)
        self.btn_last.pack(side=tk.LEFT, padx=3)

        self.btn_reset = tk.Button(ctrl_bar, text="↺ Restart", command=self.reset_sim, **btn_style)
        self.btn_reset.pack(side=tk.LEFT, padx=3)

        # Speed control
        spd_frame = tk.Frame(ctrl_bar, bg="#0F172A")
        spd_frame.pack(side=tk.RIGHT, padx=6)

        tk.Label(spd_frame, text="Speed:", font=("Helvetica", 9), fg="#94A3B8", bg="#0F172A").pack(side=tk.LEFT, padx=4)
        self.speed_scale = tk.Scale(
            spd_frame, from_=500, to=2500, orient=tk.HORIZONTAL,
            showvalue=0, command=self._on_speed_change,
            bg="#1E293B", fg="#FFFFFF", highlightthickness=0, length=100
        )
        self.speed_scale.set(1200)
        self.speed_scale.pack(side=tk.LEFT)
        self.speed_label = tk.Label(spd_frame, text="1.2s", font=("Helvetica", 9), fg="#CBD5E1", bg="#0F172A", width=5)
        self.speed_label.pack(side=tk.LEFT, padx=2)

        # Step badge & Progress Bar
        info_bar = tk.Frame(self, bg="#F1F5F9", padx=16, pady=8)
        info_bar.pack(fill=tk.X)

        self.lbl_step_counter = tk.Label(
            info_bar, text="Ready to simulate — Click ▶ Play or Next",
            font=("Helvetica", 11, "bold"), fg="#0F172A", bg="#F1F5F9"
        )
        self.lbl_step_counter.pack(side=tk.LEFT)

        self.prog_bar = ttk.Progressbar(info_bar, orient=tk.HORIZONTAL, mode='determinate', length=220)
        self.prog_bar.pack(side=tk.RIGHT)

        # 2. Main Visual Staging Area
        stage_container = tk.Frame(self, bg="#F8FAFC", padx=16, pady=12)
        stage_container.pack(fill=tk.BOTH, expand=True)

        # Staging Card
        self.card = tk.Frame(stage_container, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1")
        self.card.pack(fill=tk.X, pady=(0, 12))

        card_header = tk.Frame(self.card, bg="#1E293B", padx=12, pady=8)
        card_header.pack(fill=tk.X)

        self.lbl_card_title = tk.Label(
            card_header, text="Step Evaluation Details",
            font=("Helvetica", 11, "bold"), fg="#FFFFFF", bg="#1E293B"
        )
        self.lbl_card_title.pack(side=tk.LEFT)

        self.badge_status = tk.Label(
            card_header, text="STANDBY", font=("Helvetica", 9, "bold"),
            fg="#FFFFFF", bg="#475569", padx=8, pady=2
        )
        self.badge_status.pack(side=tk.RIGHT)

        # Evaluation content
        self.eval_frame = tk.Frame(self.card, bg="#FFFFFF", padx=16, pady=14)
        self.eval_frame.pack(fill=tk.X)

        # Stage 1: Comparison
        self.lbl_stage_process = tk.Label(
            self.eval_frame, text="Process: —",
            font=("Helvetica", 13, "bold"), fg="#0F172A", bg="#FFFFFF", anchor="w"
        )
        self.lbl_stage_process.pack(fill=tk.X, pady=(0, 6))

        self.lbl_stage_check = tk.Label(
            self.eval_frame,
            text="Safety Test: Need ≤ Work condition check will appear here.",
            font=("Helvetica", 11), fg="#334155", bg="#F1F5F9",
            padx=10, pady=8, anchor="w", relief=tk.SOLID, borderwidth=1
        )
        self.lbl_stage_check.pack(fill=tk.X, pady=4)

        # Stage 2: Staged Release
        self.lbl_stage_release = tk.Label(
            self.eval_frame,
            text="Resource Return: When process finishes, its allocation is added back to Work.",
            font=("Helvetica", 11), fg="#0284C7", bg="#E0F2FE",
            padx=10, pady=8, anchor="w", relief=tk.SOLID, borderwidth=1
        )
        self.lbl_stage_release.pack(fill=tk.X, pady=4)

        # Vectors preview
        vec_frame = tk.Frame(self.eval_frame, bg="#FFFFFF")
        vec_frame.pack(fill=tk.X, pady=(8, 0))

        self.lbl_work_vec = tk.Label(
            vec_frame, text="Current Work: —",
            font=("Helvetica", 10, "bold"), fg="#0F172A", bg="#FFFFFF"
        )
        self.lbl_work_vec.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_finish_vec = tk.Label(
            vec_frame, text="Finish Status: —",
            font=("Helvetica", 10, "bold"), fg="#475569", bg="#FFFFFF"
        )
        self.lbl_finish_vec.pack(side=tk.LEFT)

        # 3. Accumulated Safe Sequence Display
        seq_box = tk.Frame(stage_container, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1", padx=14, pady=10)
        seq_box.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            seq_box, text="Current Safe Sequence Progress:",
            font=("Helvetica", 10, "bold"), fg="#334155", bg="#FFFFFF"
        ).pack(anchor="w", pady=(0, 6))

        self.seq_display_frame = tk.Frame(seq_box, bg="#FFFFFF")
        self.seq_display_frame.pack(fill=tk.X)

        self.lbl_empty_seq = tk.Label(
            self.seq_display_frame, text="< None yet >",
            font=("Helvetica", 10, "italic"), fg="#94A3B8", bg="#FFFFFF"
        )
        self.lbl_empty_seq.pack(side=tk.LEFT)

        # 4. Final Verdict Banner (shown when simulation reaches end)
        self.banner = tk.Frame(stage_container, bg="#F1F5F9", highlightthickness=1, highlightbackground="#CBD5E1", padx=14, pady=10)
        self.banner.pack(fill=tk.X)

        self.lbl_banner_title = tk.Label(
            self.banner, text="Final Safety Result",
            font=("Helvetica", 11, "bold"), fg="#0F172A", bg="#F1F5F9", anchor="w"
        )
        self.lbl_banner_title.pack(fill=tk.X)

        self.lbl_banner_desc = tk.Label(
            self.banner, text="Run the simulation to inspect the complete deadlock avoidance verdict.",
            font=("Helvetica", 10), fg="#334155", bg="#F1F5F9", justify=tk.LEFT, wraplength=700, anchor="w"
        )
        self.lbl_banner_desc.pack(fill=tk.X, pady=(4, 0))

    def _on_speed_change(self, val):
        self.speed_ms = int(val)
        self.speed_label.config(text=f"{self.speed_ms / 1000:.1f}s")

    def load_safety_result(self, result: SafetyResult):
        """Loads a new safety result and resets stepper to initial position."""
        self.pause()
        self.safety_result = result
        self.reset_sim()

    def reset_sim(self):
        """Resets to step 0 (initial available work, empty sequence)."""
        self.pause()
        self.current_step_idx = -1
        self._update_view()

    def go_first(self):
        self.pause()
        if self.safety_result and self.safety_result.steps:
            self.current_step_idx = 0
            self._update_view()

    def go_prev(self):
        self.pause()
        if self.current_step_idx > -1:
            self.current_step_idx -= 1
            self._update_view()

    def go_next(self):
        self.pause()
        if not self.safety_result or not self.safety_result.steps:
            return
        total_steps = len(self.safety_result.steps)
        if self.current_step_idx < total_steps - 1:
            self.current_step_idx += 1
            self._update_view()

    def go_last(self):
        self.pause()
        if self.safety_result and self.safety_result.steps:
            self.current_step_idx = len(self.safety_result.steps) - 1
            self._update_view()

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        if not self.safety_result or not self.safety_result.steps:
            return
        # If at last step, restart
        if self.current_step_idx >= len(self.safety_result.steps) - 1:
            self.current_step_idx = -1

        self.is_playing = True
        self.btn_play.config(text="⏸ Pause", bg="#D97706", activebackground="#B45309")
        self._step_timer()

    def pause(self):
        self.is_playing = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.btn_play.config(text="▶ Play", bg="#0284C7", activebackground="#0369A1")

    def _step_timer(self):
        if not self.is_playing or not self.safety_result:
            return
        total_steps = len(self.safety_result.steps)
        if self.current_step_idx < total_steps - 1:
            self.current_step_idx += 1
            self._update_view()
            self.timer_id = self.after(self.speed_ms, self._step_timer)
        else:
            self.pause()

    def _update_view(self):
        if not self.safety_result:
            self.lbl_step_counter.config(text="No safety calculation available. Run algorithm first.")
            return

        total_steps = len(self.safety_result.steps)

        # Progress bar
        if total_steps > 0:
            pct = max(0, int(((self.current_step_idx + 1) / total_steps) * 100))
            self.prog_bar['value'] = pct
        else:
            self.prog_bar['value'] = 0

        # Step counter label
        if self.current_step_idx == -1:
            self.lbl_step_counter.config(
                text=f"Initial State: Work = {self.safety_result.initial_available} | 0 of {total_steps} steps taken"
            )
            self.lbl_card_title.config(text="Initial System State (Before Process Evaluation)")
            self.badge_status.config(text="INITIALIZED", bg="#475569")
            self.lbl_stage_process.config(text="Initial System Available Vector")
            self.lbl_stage_check.config(
                text=f"Work is initialized to Available resources: {self.safety_result.initial_available}",
                bg="#F1F5F9", fg="#1E293B"
            )
            self.lbl_stage_release.config(
                text="Waiting to evaluate first candidate process where Need ≤ Work...",
                bg="#F8FAFC", fg="#64748B"
            )
            self.lbl_work_vec.config(text=f"Current Work: {self.safety_result.initial_available}")
            self.lbl_finish_vec.config(text=f"Finish: {[False] * len(self.safety_result.unfinished_processes + self.safety_result.safe_sequence)}")
        else:
            step: StepTrace = self.safety_result.steps[self.current_step_idx]
            self.lbl_step_counter.config(
                text=f"Step {self.current_step_idx + 1} of {total_steps}: Process {step.process_name} Selected"
            )
            self.lbl_card_title.config(text=f"Step {self.current_step_idx + 1}: Evaluating Process {step.process_name}")
            self.badge_status.config(text="SATISFIED & FINISHED", bg="#0284C7")

            self.lbl_stage_process.config(text=f"Process {step.process_name} (Index {step.process_index})")
            self.lbl_stage_check.config(
                text=f"✔ Safety Test Passed: Need {step.need} ≤ Work {step.work_before} for all resources.",
                bg="#E0F2FE", fg="#0369A1"
            )
            self.lbl_stage_release.config(
                text=f"↺ Resource Return: {step.process_name} terminates safely. Allocation {step.allocation} added to Work. New Work = {step.work_after}",
                bg="#EFF6FF", fg="#1D4ED8"
            )
            self.lbl_work_vec.config(text=f"Current Work: {step.work_after}")
            self.lbl_finish_vec.config(text=f"Finish: {step.finish_status}")

        # Update accumulated safe sequence pills
        for widget in self.seq_display_frame.winfo_children():
            widget.destroy()

        if self.current_step_idx == -1:
            lbl = tk.Label(self.seq_display_frame, text="< Simulation not started yet >", font=("Helvetica", 10, "italic"), fg="#94A3B8", bg="#FFFFFF")
            lbl.pack(side=tk.LEFT)
        else:
            for idx in range(self.current_step_idx + 1):
                p_name = self.safety_result.steps[idx].process_name
                pill = tk.Label(
                    self.seq_display_frame, text=f" {p_name} ",
                    font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#0F172A",
                    padx=6, pady=2, relief=tk.FLAT
                )
                pill.pack(side=tk.LEFT, padx=2)

                if idx < self.current_step_idx:
                    arr = tk.Label(self.seq_display_frame, text="➔", font=("Helvetica", 11), fg="#38BDF8", bg="#FFFFFF")
                    arr.pack(side=tk.LEFT, padx=2)

        # Update Final Banner
        if self.current_step_idx == total_steps - 1 or total_steps == 0:
            if self.safety_result.is_safe:
                self.banner.config(bg="#E0F2FE", highlightbackground="#38BDF8")
                self.lbl_banner_title.config(text="✔ " + self.safety_result.summary_title, fg="#0369A1", bg="#E0F2FE")
                self.lbl_banner_desc.config(text=self.safety_result.summary_message, fg="#0F172A", bg="#E0F2FE")
            else:
                self.banner.config(bg="#FFE4E6", highlightbackground="#FDA4AF")
                self.lbl_banner_title.config(text="✖ " + self.safety_result.summary_title, fg="#BE123C", bg="#FFE4E6")
                self.lbl_banner_desc.config(text=self.safety_result.summary_message, fg="#881337", bg="#FFE4E6")
        else:
            self.banner.config(bg="#F1F5F9", highlightbackground="#CBD5E1")
            self.lbl_banner_title.config(text="Simulation in Progress...", fg="#334155", bg="#F1F5F9")
            self.lbl_banner_desc.config(text="Step forward or click Play to complete the safety trace.", fg="#64748B", bg="#F1F5F9")

        # Notify parent if callback provided
        if self.on_step_change:
            self.on_step_change(self.current_step_idx)
