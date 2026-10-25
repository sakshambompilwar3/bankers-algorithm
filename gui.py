"""
Banker's Algorithm Simulator — Main GUI Window
----------------------------------------------
Professional, polished desktop interface built with Tkinter & ttk.
Features:
- Navy-blue, white, and light-blue palette
- Top summary dashboard cards (Process count, Resource types, System status, Available vector)
- Dynamically resizable tables with data preservation and confirmation
- Interactive simulation stepper with staged resource release animation
- Resource request testing with rollback guarantee
- Pure-Python Canvas resource distribution chart
- Exporting to CSV, formatted text report, and JSON persistence
- Educational OS deadlock avoidance theory guide
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

from scenario_manager import ScenarioManager
from banker_algorithm import (
    get_classic_safe_preset,
    get_classic_unsafe_preset,
    get_zero_need_preset,
    generate_random_valid_scenario
)
from matrix_tables import MatrixEditor
from simulation_stepper import SimulationStepper
from request_tester import RequestTester
from chart_canvas import ResourceBarChart


class BankersSimulatorApp(tk.Tk):
    """Main Application Window for Banker's Algorithm Simulator."""

    def __init__(self):
        super().__init__()

        self.title("Banker's Algorithm Simulator — OS Resource Management")
        self.geometry("1150x800")
        self.minsize(980, 680)

        # Initialize Scenario Manager with default classic safe preset
        self.mgr = ScenarioManager(get_classic_safe_preset())

        # Setup styling
        self._setup_styles()

        # Build UI layout
        self._build_header()
        self._build_dashboard_cards()
        self._build_notebook_tabs()
        self._build_menu()

        # Initial display sync
        self.refresh_all_views()

        # Run safety algorithm on initial preset so user starts with a ready-to-explore state
        self.on_run_algorithm(silent=True)

    def _setup_styles(self):
        self.configure(bg="#F1F5F9")

        self.style = ttk.Style(self)
        # Use clam theme for predictable color customization
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # Configure Notebook
        self.style.configure(
            "TNotebook",
            background="#0F172A",
            tabmargins=[10, 8, 10, 0]
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Helvetica", 11, "bold"),
            padding=[16, 8],
            background="#1E293B",
            foreground="#94A3B8"
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#F8FAFC"), ("active", "#334155")],
            foreground=[("selected", "#0F172A"), ("active", "#FFFFFF")]
        )

        # Configure Scrollbars & Progressbars
        self.style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#E2E8F0",
            background="#0284C7"
        )

    def _build_header(self):
        """Top navy-blue branding banner."""
        header_frame = tk.Frame(self, bg="#0F172A", padx=20, pady=12)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="Banker's Algorithm Simulator",
            font=("Helvetica", 17, "bold"),
            fg="#FFFFFF",
            bg="#0F172A"
        )
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = tk.Label(
            header_frame,
            text="— OS Deadlock Avoidance & Resource Management",
            font=("Helvetica", 12),
            fg="#38BDF8",
            bg="#0F172A"
        )
        sub_lbl.pack(side=tk.LEFT, padx=(8, 0), pady=(3, 0))

        # Quick preset dropdown in header
        quick_frame = tk.Frame(header_frame, bg="#0F172A")
        quick_frame.pack(side=tk.RIGHT)

        tk.Label(quick_frame, text="Preset:", font=("Helvetica", 10), fg="#94A3B8", bg="#0F172A").pack(side=tk.LEFT, padx=4)

        self.preset_var = tk.StringVar(value="Classic Safe (5x3)")
        presets = ["Classic Safe (5x3)", "Unsafe State (4x3)", "Zero-Need Process (3x2)", "Random Scenario"]
        self.preset_combo = ttk.Combobox(quick_frame, textvariable=self.preset_var, values=presets, state="readonly", width=18)
        self.preset_combo.pack(side=tk.LEFT, padx=4)
        self.preset_combo.bind("<<ComboboxSelected>>", lambda e: self._on_preset_dropdown())

        btn_load = tk.Button(
            quick_frame, text="Load", command=self._on_preset_dropdown,
            font=("Helvetica", 9, "bold"), fg="#FFFFFF", bg="#2563EB",
            activebackground="#1D4ED8", activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=8, pady=3, cursor="hand2"
        )
        btn_load.pack(side=tk.LEFT, padx=4)

    def _build_dashboard_cards(self):
        """Summary dashboard cards showing process count, resource types, system state, and available vector."""
        cards_container = tk.Frame(self, bg="#F1F5F9", padx=16, pady=10)
        cards_container.pack(fill=tk.X)

        # Helper to create a clean card
        def make_card(parent, title, value_init, color="#0F172A"):
            card = tk.Frame(parent, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1", padx=14, pady=8)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            t_lbl = tk.Label(card, text=title, font=("Helvetica", 9, "bold"), fg="#64748B", bg="#FFFFFF")
            t_lbl.pack(anchor="w")
            v_lbl = tk.Label(card, text=value_init, font=("Helvetica", 14, "bold"), fg=color, bg="#FFFFFF")
            v_lbl.pack(anchor="w", pady=(2, 0))
            return v_lbl

        self.card_n = make_card(cards_container, "TOTAL PROCESSES (n)", f"{self.mgr.n} Processes")
        self.card_m = make_card(cards_container, "RESOURCE TYPES (m)", f"{self.mgr.m} Types")
        self.card_status = make_card(cards_container, "SYSTEM SAFETY STATE", "READY", "#0284C7")
        self.card_avail = make_card(cards_container, "CURRENT AVAILABLE", str(self.mgr.available), "#0F172A")

    def _build_notebook_tabs(self):
        """Builds the 6 primary feature tabs."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # Tab 1: Configuration & Dynamic Input
        self.tab_config = tk.Frame(self.notebook, bg="#F8FAFC")
        self.notebook.add(self.tab_config, text=" ⚙️ Matrix Input & Setup ")

        # Tab 2: Interactive Simulation Stepper
        self.tab_sim = tk.Frame(self.notebook, bg="#F8FAFC")
        self.notebook.add(self.tab_sim, text=" 🎬 Simulation & Stepper ")

        # Tab 3: Resource Request Testing
        self.tab_request = tk.Frame(self.notebook, bg="#F8FAFC")
        self.notebook.add(self.tab_request, text=" 🔍 Resource Request ")

        # Tab 4: Resource Distribution Chart
        self.tab_chart = tk.Frame(self.notebook, bg="#F8FAFC")
        self.notebook.add(self.tab_chart, text=" 📊 Resource Analytics ")

        # Tab 5: Comprehensive Matrices & Log
        self.tab_tables = tk.Frame(self.notebook, bg="#F8FAFC")
        self.notebook.add(self.tab_tables, text=" 📋 Complete Matrix Tables ")

        # Tab 6: Educational Guide & Theory
        self.tab_theory = tk.Frame(self.notebook, bg="#F8FAFC")
        self.notebook.add(self.tab_theory, text=" 📘 OS Theory & Concepts ")

        # Populate each tab
        self._init_tab_config()
        self._init_tab_sim()
        self._init_tab_request()
        self._init_tab_chart()
        self._init_tab_tables()
        self._init_tab_theory()

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # -------------------------------------------------------------------------
    # TAB 1: Dynamic Configuration & Input
    # -------------------------------------------------------------------------
    def _init_tab_config(self):
        # Action & Dimension Toolbar
        toolbar = tk.Frame(self.tab_config, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1", padx=16, pady=10)
        toolbar.pack(fill=tk.X, padx=16, pady=(14, 10))

        # Dimensions Controls
        dim_frame = tk.Frame(toolbar, bg="#FFFFFF")
        dim_frame.pack(side=tk.LEFT)

        # Processes n
        tk.Label(dim_frame, text="Processes (n):", font=("Helvetica", 10, "bold"), fg="#1E293B", bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 4))
        self.spin_n = tk.Spinbox(dim_frame, from_=1, to=20, width=4, font=("Helvetica", 10), justify="center")
        self.spin_n.delete(0, tk.END)
        self.spin_n.insert(0, str(self.mgr.n))
        self.spin_n.pack(side=tk.LEFT, padx=(0, 4))

        btn_add_p = tk.Button(dim_frame, text="+", command=self.on_add_process, font=("Helvetica", 9, "bold"), bg="#E2E8F0", relief=tk.FLAT, padx=6)
        btn_add_p.pack(side=tk.LEFT, padx=1)
        btn_rem_p = tk.Button(dim_frame, text="−", command=self.on_remove_process, font=("Helvetica", 9, "bold"), bg="#E2E8F0", relief=tk.FLAT, padx=6)
        btn_rem_p.pack(side=tk.LEFT, padx=(1, 14))

        # Resources m
        tk.Label(dim_frame, text="Resources (m):", font=("Helvetica", 10, "bold"), fg="#1E293B", bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 4))
        self.spin_m = tk.Spinbox(dim_frame, from_=1, to=10, width=4, font=("Helvetica", 10), justify="center")
        self.spin_m.delete(0, tk.END)
        self.spin_m.insert(0, str(self.mgr.m))
        self.spin_m.pack(side=tk.LEFT, padx=(0, 4))

        btn_add_r = tk.Button(dim_frame, text="+", command=self.on_add_resource, font=("Helvetica", 9, "bold"), bg="#E2E8F0", relief=tk.FLAT, padx=6)
        btn_add_r.pack(side=tk.LEFT, padx=1)
        btn_rem_r = tk.Button(dim_frame, text="−", command=self.on_remove_resource, font=("Helvetica", 9, "bold"), bg="#E2E8F0", relief=tk.FLAT, padx=6)
        btn_rem_r.pack(side=tk.LEFT, padx=(1, 14))

        btn_apply_dim = tk.Button(
            dim_frame, text="Apply Dimensions", command=self.on_apply_dimensions,
            font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#0284C7",
            activebackground="#0369A1", activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        )
        btn_apply_dim.pack(side=tk.LEFT, padx=4)

        # Primary Action Buttons on the Right
        act_frame = tk.Frame(toolbar, bg="#FFFFFF")
        act_frame.pack(side=tk.RIGHT)

        btn_run = tk.Button(
            act_frame, text="▶ Run Safety Algorithm", command=self.on_run_algorithm,
            font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#2563EB",
            activebackground="#1D4ED8", activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=14, pady=4, cursor="hand2"
        )
        btn_run.pack(side=tk.LEFT, padx=4)

        btn_reset = tk.Button(
            act_frame, text="↺ Reset", command=self.on_reset_form,
            font=("Helvetica", 10), fg="#0F172A", bg="#E2E8F0",
            activebackground="#CBD5E1", relief=tk.FLAT, padx=8, pady=4, cursor="hand2"
        )
        btn_reset.pack(side=tk.LEFT, padx=4)

        # Matrix Editing Area
        self.matrix_editor = MatrixEditor(
            self.tab_config,
            self.mgr,
            on_change_callback=self._on_matrix_data_changed
        )
        self.matrix_editor.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))

    # -------------------------------------------------------------------------
    # TAB 2: Simulation Stepper
    # -------------------------------------------------------------------------
    def _init_tab_sim(self):
        self.sim_stepper = SimulationStepper(
            self.tab_sim,
            on_step_change=self._on_sim_step_changed
        )
        self.sim_stepper.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 3: Resource Request Testing
    # -------------------------------------------------------------------------
    def _init_tab_request(self):
        self.request_tester = RequestTester(
            self.tab_request,
            self.mgr,
            on_apply_callback=self._on_request_applied
        )
        self.request_tester.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 4: Resource Analytics Chart
    # -------------------------------------------------------------------------
    def _init_tab_chart(self):
        self.chart = ResourceBarChart(self.tab_chart)
        self.chart.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 5: Complete Matrix Tables & Execution Log
    # -------------------------------------------------------------------------
    def _init_tab_tables(self):
        container = tk.Frame(self.tab_tables, bg="#F8FAFC", padx=16, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        top_actions = tk.Frame(container, bg="#F8FAFC")
        top_actions.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            top_actions, text="Complete System Matrices & Execution Log",
            font=("Helvetica", 13, "bold"), fg="#0F172A", bg="#F8FAFC"
        ).pack(side=tk.LEFT)

        btn_csv = tk.Button(
            top_actions, text="📊 Export to CSV", command=self.on_export_csv,
            font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#0284C7",
            activebackground="#0369A1", relief=tk.FLAT, padx=12, pady=4, cursor="hand2"
        )
        btn_csv.pack(side=tk.RIGHT, padx=4)

        btn_rep = tk.Button(
            top_actions, text="📄 Export Text Report", command=self.on_export_report,
            font=("Helvetica", 10, "bold"), fg="#FFFFFF", bg="#1E293B",
            activebackground="#334155", relief=tk.FLAT, padx=12, pady=4, cursor="hand2"
        )
        btn_rep.pack(side=tk.RIGHT, padx=4)

        # Text display for full report & matrices
        self.txt_full_tables = tk.Text(
            container, font=("Menlo", 10), bg="#FFFFFF", fg="#0F172A",
            highlightthickness=1, highlightbackground="#CBD5E1", relief=tk.FLAT,
            padx=14, pady=12
        )
        scroll_y = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.txt_full_tables.yview)
        self.txt_full_tables.configure(yscrollcommand=scroll_y.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_full_tables.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 6: Educational Guide & Deadlock Concepts
    # -------------------------------------------------------------------------
    def _init_tab_theory(self):
        container = tk.Frame(self.tab_theory, bg="#FFFFFF", padx=20, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        txt_theory = tk.Text(
            container, font=("Helvetica", 11), bg="#FFFFFF", fg="#1E293B",
            wrap=tk.WORD, highlightthickness=0, relief=tk.FLAT, padx=10, pady=10
        )
        scroll_y = ttk.Scrollbar(container, orient=tk.VERTICAL, command=txt_theory.yview)
        txt_theory.configure(yscrollcommand=scroll_y.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        txt_theory.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        theory_content = """BANKER'S ALGORITHM — OS RESOURCE MANAGEMENT & DEADLOCK AVOIDANCE
========================================================================================

1. INTRODUCTION & HISTORICAL BACKGROUND
---------------------------------------
The Banker's Algorithm was formulated by Edsger W. Dijkstra in 1965. It is a classic deadlock
avoidance strategy named after the banking model: a banker will never allocate cash to customers
in a way that leaves the bank unable to satisfy the maximum borrowing needs of at least one customer
who can eventually finish their business and repay their loan.

2. ESSENTIAL FORMULAS (SILBERSCHATZ MODEL)
------------------------------------------
For n processes (P0, P1, ..., Pn-1) and m resource types (R0, R1, ..., Rm-1):

• Total Instances Vector (1 × m):
    Total[j] = Total physical units of resource type j in the operating system.

• Allocation Matrix (n × m):
    Allocation[i][j] = Number of instances of resource j currently held by process Pi.

• Maximum Demand Matrix (n × m):
    Maximum[i][j] = Maximum instances of resource j that process Pi will ever require.

• Need Matrix (n × m):
    Need[i][j] = Maximum[i][j] − Allocation[i][j]
    Represents remaining resources process Pi may request to complete execution.

• Available Vector (1 × m):
    Available[j] = Total[j] − ∑ Allocation[i][j] (for all processes i = 0 to n-1)
    Represents currently free instances available for immediate allocation.

3. THE SAFETY ALGORITHM
-----------------------
Step 1: Let Work and Finish be vectors of length m and n, respectively.
        Initialize Work = Available and Finish[i] = False for all i = 0, 1, ..., n-1.

Step 2: Find an index i such that:
        a) Finish[i] == False
        b) Need[i][j] ≤ Work[j] for all j = 0, 1, ..., m-1.
        If no such process exists, proceed to Step 4.

Step 3: Process Pi can safely complete execution!
        Work = Work + Allocation[i]
        Finish[i] = True
        Add Pi to the Safe Sequence.
        Return to Step 2.

Step 4: If Finish[i] == True for all i, then the system is in a SAFE STATE.
        Otherwise, the system is in an UNSAFE STATE.

4. CRITICAL DISTINCTION: SAFE STATE vs. UNSAFE STATE vs. DEADLOCK
-----------------------------------------------------------------
• Safe State:
  A safe state is NOT just a state with free resources. It means there exists at least one order
  (a Safe Sequence) in which every process can be granted its maximum claim, terminate, and release
  all its held resources.

• Unsafe State:
  An unsafe state is NOT synonymous with an actual deadlock! An unsafe state simply means the OS
  cannot guarantee avoidance if all processes suddenly claim their maximum demand at once.
  The system might run to completion without deadlocking if processes don't ask for their full claims,
  but deadlock avoidance refuses to enter unsafe states as a defensive measure.

• Deadlock Avoidance vs. Deadlock Prevention:
  - Prevention: Restricts how requests are made by eliminating one of Coffman's 4 conditions
    (Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait).
  - Avoidance: Dynamically inspects resource allocation states to ensure a circular wait condition
    can never materialize.

5. RESOURCE-REQUEST ALGORITHM RULES
-----------------------------------
When process Pi requests vector Request[i]:
1. If Request[i][j] > Need[i][j] for any resource j:
   Raise an error (process has exceeded its maximum declared claim).
2. If Request[i][j] > Available[j] for any resource j:
   Process Pi must wait (insufficient physical resources currently available).
3. Pretend to allocate requested resources:
   Available = Available − Request[i]
   Allocation[i] = Allocation[i] + Request[i]
   Need[i] = Need[i] − Request[i]
4. Run the Safety Algorithm on the tentative state:
   - If SAFE: Officially grant the request!
   - If UNSAFE: Deny request and roll back all tentative modifications. Pi must wait.
"""
        txt_theory.insert(tk.END, theory_content)
        txt_theory.config(state=tk.DISABLED)

    # -------------------------------------------------------------------------
    # MENU BAR
    # -------------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Safe Preset (Silberschatz 5x3)", command=lambda: self.load_preset("safe"))
        file_menu.add_command(label="Load Unsafe Preset (4x3)", command=lambda: self.load_preset("unsafe"))
        file_menu.add_command(label="Load Zero-Need Preset (3x2)", command=lambda: self.load_preset("zero_need"))
        file_menu.add_command(label="Generate Random Scenario", command=lambda: self.load_preset("random"))
        file_menu.add_separator()
        file_menu.add_command(label="Save Scenario to JSON...", command=self.on_save_json)
        file_menu.add_command(label="Open Scenario from JSON...", command=self.on_load_json)
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV...", command=self.on_export_csv)
        file_menu.add_command(label="Export Text Report...", command=self.on_export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Scenarios Menu
        scen_menu = tk.Menu(menubar, tearoff=0)
        scen_menu.add_command(label="Run Safety Algorithm", command=self.on_run_algorithm)
        scen_menu.add_command(label="Reset Form to Defaults", command=self.on_reset_form)
        menubar.add_cascade(label="Scenario", menu=scen_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About Banker's Algorithm", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _show_about(self):
        messagebox.showinfo(
            "About Banker's Algorithm Simulator",
            "Banker's Algorithm Simulator — OS Resource Management\n\n"
            "An interactive desktop educational application demonstrating Dijkstra's classic "
            "deadlock avoidance algorithm for Operating Systems.\n\n"
            "Features:\n"
            "• Dynamic process and resource configuration\n"
            "• Step-by-step interactive simulation player\n"
            "• Safe vs. Unsafe state classification\n"
            "• Resource request testing with automatic rollback\n"
            "• Native Canvas utilization chart\n"
            "• CSV, JSON, and text report export\n"
        )

    # -------------------------------------------------------------------------
    # SYNCHRONIZATION & EVENT HANDLERS
    # -------------------------------------------------------------------------
    def refresh_all_views(self):
        """Synchronizes dashboard cards, matrix tables, stepper, and chart."""
        # Update spinboxes
        self.spin_n.delete(0, tk.END)
        self.spin_n.insert(0, str(self.mgr.n))
        self.spin_m.delete(0, tk.END)
        self.spin_m.insert(0, str(self.mgr.m))

        # Update Dashboard cards
        self.card_n.config(text=f"{self.mgr.n} Processes")
        self.card_m.config(text=f"{self.mgr.m} Types")
        self.card_avail.config(text=str(self.mgr.available))

        if self.mgr.is_outdated:
            self.card_status.config(text="OUTDATED", fg="#D97706")
        elif self.mgr.safety_result:
            if self.mgr.safety_result.is_safe:
                self.card_status.config(text="SAFE STATE", fg="#0284C7")
            else:
                self.card_status.config(text="UNSAFE STATE", fg="#BE123C")
        else:
            self.card_status.config(text="READY", fg="#475569")

        # Refresh tables
        self.matrix_editor.rebuild_tables()

        # Refresh chart
        self.chart.update_data(
            self.mgr.resource_names,
            self.mgr.total,
            self.mgr.allocation,
            self.mgr.available
        )

        # Refresh request tester
        self.request_tester.refresh_scenario()

        # Refresh full tables text tab
        self._refresh_full_tables_tab()

    def _refresh_full_tables_tab(self):
        self.txt_full_tables.delete("1.0", tk.END)
        report_text = self.mgr.generate_text_report()
        self.txt_full_tables.insert(tk.END, report_text)

    def _on_matrix_data_changed(self):
        """Called whenever a table cell or label is modified by the user."""
        self.card_avail.config(text=str(self.mgr.available))
        self.card_status.config(text="OUTDATED", fg="#D97706")
        self.chart.update_data(
            self.mgr.resource_names,
            self.mgr.total,
            self.mgr.allocation,
            self.mgr.available
        )
        self._refresh_full_tables_tab()

    def _on_tab_changed(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if "Analytics" in selected_tab:
            self.chart.draw()
        elif "Complete Matrix" in selected_tab:
            self._refresh_full_tables_tab()

    def _on_preset_dropdown(self):
        selected = self.preset_var.get()
        if "Safe" in selected:
            self.load_preset("safe")
        elif "Unsafe" in selected:
            self.load_preset("unsafe")
        elif "Zero-Need" in selected:
            self.load_preset("zero_need")
        elif "Random" in selected:
            self.load_preset("random")

    def load_preset(self, preset_key: str):
        if preset_key == "safe":
            data = get_classic_safe_preset()
        elif preset_key == "unsafe":
            data = get_classic_unsafe_preset()
        elif preset_key == "zero_need":
            data = get_zero_need_preset()
        elif preset_key == "random":
            data = generate_random_valid_scenario(self.mgr.n, self.mgr.m)
        else:
            return

        self.mgr.load_from_dict(data)
        self.refresh_all_views()
        self.on_run_algorithm(silent=True)

    def on_apply_dimensions(self):
        """Resizes the matrices based on spinbox values with confirmation on data loss."""
        try:
            new_n = int(self.spin_n.get().strip())
            new_m = int(self.spin_m.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Process count (n) and Resource count (m) must be integers.")
            return

        if new_n < 1 or new_m < 1:
            messagebox.showerror("Invalid Dimensions", "Dimensions must be ≥ 1.")
            return

        def confirm_shrink(loss_msg: str) -> bool:
            return messagebox.askyesno(
                "Confirm Shrinking Dimensions",
                f"{loss_msg}\n\nAre you sure you want to permanently discard this data?"
            )

        success = self.mgr.resize(new_n, new_m, confirm_callback=confirm_shrink)
        if success:
            self.refresh_all_views()
            self.on_run_algorithm(silent=True)

    def on_add_process(self):
        self.mgr.add_process()
        self.refresh_all_views()

    def on_remove_process(self):
        def confirm_shrink(loss_msg: str) -> bool:
            return messagebox.askyesno("Confirm Removal", f"{loss_msg}\n\nDelete this process row?")

        self.mgr.remove_process(confirm_callback=confirm_shrink)
        self.refresh_all_views()

    def on_add_resource(self):
        self.mgr.add_resource()
        self.refresh_all_views()

    def on_remove_resource(self):
        def confirm_shrink(loss_msg: str) -> bool:
            return messagebox.askyesno("Confirm Removal", f"{loss_msg}\n\nDelete this resource column?")

        self.mgr.remove_resource(confirm_callback=confirm_shrink)
        self.refresh_all_views()

    def on_run_algorithm(self, silent: bool = False):
        """Executes Banker's Safety Algorithm and updates Stepper and Cards."""
        ok, err, safety_res = self.mgr.execute_safety_algorithm()
        if not ok:
            if not silent:
                messagebox.showerror("Validation Error", err)
            self.card_status.config(text="ERROR", fg="#BE123C")
            return

        # Update Stepper
        self.sim_stepper.load_safety_result(safety_res)

        # Update Cards
        if safety_res.is_safe:
            self.card_status.config(text="SAFE STATE", fg="#0284C7")
        else:
            self.card_status.config(text="UNSAFE STATE", fg="#BE123C")

        self.card_avail.config(text=str(self.mgr.available))
        self._refresh_full_tables_tab()

        if not silent:
            # Switch to Simulation tab to showcase result
            self.notebook.select(self.tab_sim)

    def on_reset_form(self):
        confirmed = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all inputs and configuration back to the default classic safe scenario?"
        )
        if confirmed:
            self.load_preset("safe")

    def _on_sim_step_changed(self, step_idx: int):
        """Highlights the currently evaluated process row in the matrix editor."""
        if self.mgr.safety_result and step_idx >= 0 and step_idx < len(self.mgr.safety_result.steps):
            step = self.mgr.safety_result.steps[step_idx]
            self.matrix_editor.highlight_process_row(step.process_index)
        else:
            self.matrix_editor.highlight_process_row(-1)

    def _on_request_applied(self):
        self.refresh_all_views()
        self.notebook.select(self.tab_config)

    def on_save_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Scenario as JSON"
        )
        if path:
            try:
                self.mgr.save_to_json(path)
                messagebox.showinfo("Saved", f"Scenario successfully saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

    def on_load_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Load Scenario from JSON"
        )
        if path:
            try:
                self.mgr.load_from_json(path)
                self.refresh_all_views()
                self.on_run_algorithm(silent=True)
                messagebox.showinfo("Loaded", f"Scenario successfully loaded from:\n{path}")
            except Exception as e:
                messagebox.showerror("Load Error", str(e))

    def on_export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Export Scenario to CSV"
        )
        if path:
            try:
                self.mgr.export_to_csv(path)
                messagebox.showinfo("Exported", f"Data exported successfully to CSV:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    def on_export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Markdown", "*.md"), ("All Files", "*.*")],
            title="Export Scenario Report"
        )
        if path:
            try:
                report = self.mgr.generate_text_report()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(report)
                messagebox.showinfo("Exported", f"Report exported successfully:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
