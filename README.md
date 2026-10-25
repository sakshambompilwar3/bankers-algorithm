# Banker’s Algorithm Simulator — OS Resource Management

An interactive, beginner-friendly desktop application developed in **Python 3** and **Tkinter/ttk** for visualizing and understanding **Dijkstra's Banker's Algorithm** for deadlock avoidance in Operating Systems.

Designed for college mini-projects, OS lab demonstrations, viva preparation, and self-study, this simulator pairs a modern **navy-blue & light-blue GUI** with dynamic matrix configuration, step-by-step playback, resource request simulations with rollback guarantees, and native canvas-based resource analytics.

---

## 📸 Key Features

1. **Fully Dynamic Process & Resource Management**:
   - Change process count ($n$) and resource types ($m$) at any time.
   - Expand or shrink matrices while **preserving all existing user-entered cells**.
   - Confirmation prompts protect against accidental data loss when reducing dimensions.
   - Custom naming for processes (e.g., `P0`, `P1`, `WorkerA`) and resources (e.g., `CPU`, `RAM`, `Disk`).

2. **Step-by-Step Simulation Stepper**:
   - Interactive playback controls: `First`, `Prev`, `Play / Pause`, `Next`, `Last`, `Restart`.
   - Adjustable simulation delay (0.5s – 2.5s).
   - Dynamic highlighting of evaluated processes.
   - Clear breakdown of the $\text{Need} \le \text{Work}$ condition check.
   - Animated staged release of resources ($\text{Work}_{\text{new}} = \text{Work}_{\text{old}} + \text{Allocation}$).
   - Live Safe Sequence accumulator showing visual progress pills.

3. **Resource Request Simulation & Rollback**:
   - Select any process and test an immediate resource request vector.
   - Evaluates all three Banker's rules:
     - **Phase 1**: $\text{Request} \le \text{Need}$ (Checks against declared maximum demand).
     - **Phase 2**: $\text{Request} \le \text{Available}$ (Checks current system free capacity).
     - **Phase 3**: Tentative Allocation & Safety Check.
   - If granting the request leads to an unsafe state, **all tentative modifications are immediately rolled back**, preserving original data without corruption.
   - One-click option to officially apply granted requests to the active scenario.

4. **Resource Analytics Chart (Zero-Dependency Native Canvas)**:
   - High-performance, responsive grouped bar chart drawn directly on a Tkinter `Canvas`.
   - Compares **Total Instances**, **Allocated**, and **Available** per resource.
   - Displays real-time utilization percentages without needing `matplotlib` or external packages.

5. **Data Export & Persistence**:
   - **Save & Load Scenario**: JSON serialization for easy lab submission and grading.
   - **CSV Export**: Matrix tables and step-by-step execution trace in standard CSV format.
   - **Detailed Text Report**: Formatted ASCII tables with full mathematical trace and OS concepts.

6. **Educational OS Theory & Deadlock Terminology**:
   - Distinguishes **Deadlock Avoidance** vs. **Deadlock Prevention** vs. **Deadlock Detection**.
   - Clarifies the essential OS distinction: **An Unsafe State is NOT necessarily a Deadlock** (it indicates that safe completion cannot be guaranteed if all processes simultaneously demand their maximum claim).

---

## 🛠️ Project Structure

```
bankers_algorithm_simulator/
├── main.py                 # Application launcher & macOS environment configuration
├── gui.py                  # Main GUI window, tab coordinator, and summary dashboard
├── banker_algorithm.py     # Pure algorithmic logic: Need, Available, Safety & Request
├── scenario_manager.py     # Dynamic matrix sizing, data preservation, and exports
├── matrix_tables.py        # Scrollable, editable input grids with real-time recalculation
├── simulation_stepper.py   # Visual stepper controls, Need<=Work check, and staged release
├── request_tester.py       # 3-phase request evaluation panel with rollback guarantee
├── chart_canvas.py         # Pure-Python Tkinter Canvas resource distribution chart
├── validation.py           # Strict mathematical and logical matrix validator
├── requirements.txt        # Zero external dependencies (standard Python 3)
├── data/                   # Bundled scenario JSON files
│   ├── classic_silberschatz_safe.json
│   ├── unsafe_scenario.json
│   └── large_dynamic_scenario.json
└── tests/                  # Automated unit and integration test suite
    ├── test_banker.py
    ├── test_dynamic_config.py
    └── test_gui_integration.py
```

---

## 🚀 Installation & Execution on macOS

### Prerequisites
- macOS 10.14 or later.
- Python 3.8+ (macOS includes Python 3 or install via Homebrew / python.org).

### Step 1: Navigate to the Project Directory
```bash
cd /Users/sakshambompilwar/.gemini/antigravity/scratch/bankers_algorithm_simulator
```

### Step 2: (Optional) Verify Python and Tkinter
Tkinter comes pre-installed with standard Python distributions on macOS:
```bash
python3 -c "import tkinter; print('Tkinter is ready!')"
```

### Step 3: Run the Application

You can run the project in multiple ways:

#### Option A: Cinematic Mission Control Web UI (Recommended)
Launch the full interactive Mission Control experience:
```bash
python3 app.py
```
This automatically launches the server and opens your default browser at:
👉 **[http://localhost:8080](http://localhost:8080)**

*(Use `python3 app.py --no-open` to start the server without auto-opening the browser).*

#### Option B: Standalone Web Server
```bash
python3 web_server.py 8080
```

#### Option C: Native Desktop GUI (Tkinter)
Launch the desktop Tkinter interface:
```bash
python3 main.py
```

*Note: The script automatically silences macOS system Tkinter deprecation notices for clean terminal output.*

---

## 🧪 Automated Testing

The project includes 32 automated unit and integration tests covering:
- Correctness of $\text{Need}$ and $\text{Available}$ calculations.
- Known safe states (Silberschatz 5×3 textbook example).
- Known unsafe states and blocked process detection.
- Invalid input validation (negative numbers, $\text{Allocation} > \text{Maximum}$, over-allocated totals).
- Edge cases (processes needing 0 additional resources, $1 \times 1$ matrices).
- Resource requests: Granted, Denied (exceeds need), Denied (exceeds available), Denied with rollback (causes unsafe state).
- Dynamic matrix resizing ($3 \times 2 \to 7 \times 4 \to 2 \times 1$) with data preservation.
- Full GUI lifecycle and interactive widget integration.

### Run All Tests:
```bash
python3 -m unittest discover tests -v
```

### Test Output:
```
Ran 24 tests in 0.392s
OK
```

---

## 📖 Sample Input and Expected Output

### Input Scenario (Silberschatz OS Concepts)
- **Processes (5)**: `P0`, `P1`, `P2`, `P3`, `P4`
- **Resources (3)**: `A` (Total: 10), `B` (Total: 5), `C` (Total: 7)

#### Matrices:
```
Process | Allocation (A B C) | Maximum (A B C) | Need (A B C)
--------+--------------------+-----------------+-------------
P0      | 0  1  0            | 7  5  3         | 7  4  3
P1      | 2  0  0            | 3  2  2         | 1  2  2
P2      | 3  0  2            | 9  0  2         | 6  0  0
P3      | 2  1  1            | 2  2  2         | 0  1  1
P4      | 0  0  2            | 4  3  3         | 4  3  1
```

- **Initial Allocated**: $A = 7, B = 2, C = 5$
- **Initial Available**: $A = 10 - 7 = 3, B = 5 - 2 = 3, C = 7 - 5 = 2 \implies [3, 3, 2]$

### Expected Safety Algorithm Execution Trace:
1. **Work = [3, 3, 2]**:
   - Check `P0`: Need $[7, 4, 3] \le [3, 3, 2]$ is **False**.
   - Check `P1`: Need $[1, 2, 2] \le [3, 3, 2]$ is **True**!
     - `P1` executes and releases allocation $[2, 0, 0]$.
     - New Work = $[3+2, 3+0, 2+0] = [5, 3, 2]$.
     - Safe Sequence: `[P1]`
2. **Work = [5, 3, 2]**:
   - Check `P3`: Need $[0, 1, 1] \le [5, 3, 2]$ is **True**!
     - `P3` executes and releases allocation $[2, 1, 1]$.
     - New Work = $[5+2, 3+1, 2+1] = [7, 4, 3]$.
     - Safe Sequence: `[P1, P3]`
3. **Work = [7, 4, 3]**:
   - Check `P4`: Need $[4, 3, 1] \le [7, 4, 3]$ is **True**!
     - `P4` executes and releases allocation $[0, 0, 2]$.
     - New Work = $[7+0, 4+0, 3+2] = [7, 4, 5]$.
     - Safe Sequence: `[P1, P3, P4]`
4. **Work = [7, 4, 5]**:
   - Check `P0`: Need $[7, 4, 3] \le [7, 4, 5]$ is **True**!
     - `P0` executes and releases allocation $[0, 1, 0]$.
     - New Work = $[7+0, 4+1, 5+0] = [7, 5, 5]$.
     - Safe Sequence: `[P1, P3, P4, P0]`
5. **Work = [7, 5, 5]**:
   - Check `P2`: Need $[6, 0, 0] \le [7, 5, 5]$ is **True**!
     - `P2` executes and releases allocation $[3, 0, 2]$.
     - New Work = $[7+3, 5+0, 5+2] = [10, 5, 7]$ (Equals Total system resources).
     - Safe Sequence: `[P1, P3, P4, P0, P2]`

### Expected Final Verdict:
- **System State**: `SAFE`
- **Safe Sequence**: `< P1 → P3 → P4 → P0 → P2 >`

---

## 💡 Module Explanations

1. **`banker_algorithm.py`**:
   - Core mathematical engine. Contains pure functions `calculate_need`, `calculate_available`, `run_safety_algorithm`, and `simulate_resource_request`. Zero UI dependencies.

2. **`validation.py`**:
   - Input validator ensuring dimensions, non-negative numbers, capacity limits ($\sum \text{Alloc} \le \text{Total}$), and logical boundaries ($\text{Max} \ge \text{Alloc}$) are maintained.

3. **`scenario_manager.py`**:
   - State manager for the active simulation. Preserves cells on table resizing, detects potential data loss on dimension reduction, formats text reports, and exports to CSV and JSON.

4. **`matrix_tables.py`**:
   - Dynamic, scrollable UI grid allowing live editing of Total, Allocation, and Maximum Demand matrices with automatic recalculation of Need and Available previews.

5. **`simulation_stepper.py`**:
   - Visual simulation player displaying candidate process evaluation, condition check badges, staged resource addition, and safe sequence pills.

6. **`request_tester.py`**:
   - Interactive testing form for arbitrary resource requests with 3-phase rule feedback and complete rollback capability.

7. **`chart_canvas.py`**:
   - Pure-Python Tkinter Canvas chart visualizing per-resource allocation and utilization percentage without external dependencies.

8. **`gui.py`**:
   - Main window combining top metric cards, the six feature tabs, menu commands, and state synchronization.

9. **`main.py`**:
   - Application launcher configuring macOS system settings and launching the main event loop.

---

## 📋 Completed Features & Known Limitations

### Completed Features:
- [x] Modern navy-blue, white, and light-blue palette (no green dominance).
- [x] Dynamic configuration supporting arbitrary process ($1 \le n \le 20$) and resource counts ($1 \le m \le 10$).
- [x] Data preservation when expanding tables; confirmation dialogs on data loss when shrinking.
- [x] Real-time live recalculation of Need and Available as values are typed.
- [x] Interactive step-by-step playback with speed control, pause, and staged resource returns.
- [x] Comprehensive resource request testing with 3-stage validation and guaranteed rollback.
- [x] Built-in presets (Safe, Unsafe, Zero-Need, Random).
- [x] Pure-Python responsive Canvas resource utilization chart.
- [x] Export to CSV, formatted text report, and JSON scenario files.
- [x] Clear explanation of deadlock terminology (Safe vs. Unsafe vs. Deadlock).
- [x] 24 automated unit and integration tests passing with 100% success.

### Limitations:
- The GUI is optimized for up to 25 processes and 12 resource types for visual clarity on standard desktop screens (though the underlying algorithm has no dimension limit).
- Single safe sequence is displayed per run (canonical first-fit search order); while multiple safe sequences may exist for a given scenario, the first valid safe sequence is reported.
