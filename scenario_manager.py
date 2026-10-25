"""
Scenario Manager Module
-----------------------
Maintains the dynamic scenario state (n processes, m resources),
guarantees data preservation on dimensional changes, triggers recomputation,
and provides JSON, CSV, and formatted text report exports.
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
import copy
import json
import csv
from banker_algorithm import (
    calculate_need,
    calculate_available,
    run_safety_algorithm,
    simulate_resource_request,
    get_classic_safe_preset,
    get_classic_unsafe_preset,
    get_zero_need_preset,
    generate_random_valid_scenario,
    SafetyResult,
    RequestResult
)
from validation import validate_scenario


class ScenarioManager:
    """
    Manages dynamic scenario configuration, matrix data preservation,
    automatic Need & Available recomputation, and export capabilities.
    """

    def __init__(self, initial_preset: Optional[Dict[str, Any]] = None):
        if initial_preset is None:
            initial_preset = get_classic_safe_preset()
        self.load_from_dict(initial_preset)

    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """Loads a scenario from a dictionary representation."""
        self.n: int = data.get("n", len(data.get("allocation", [])))
        self.m: int = data.get("m", len(data.get("total", [])))
        self.process_names: List[str] = list(
            data.get("process_names", [f"P{i}" for i in range(self.n)])
        )
        self.resource_names: List[str] = list(
            data.get("resource_names", [chr(65 + j) if j < 26 else f"R{j}" for j in range(self.m)])
        )
        self.total: List[int] = list(data.get("total", [0] * self.m))
        self.allocation: List[List[int]] = copy.deepcopy(data.get("allocation", [[0] * self.m for _ in range(self.n)]))
        self.maximum: List[List[int]] = copy.deepcopy(data.get("maximum", [[0] * self.m for _ in range(self.n)]))

        self.title: str = data.get("title", f"Custom Scenario ({self.n} Processes, {self.m} Resources)")
        self.description: str = data.get("description", "User-configured resource management scenario.")

        self.safety_result: Optional[SafetyResult] = None
        self.request_result: Optional[RequestResult] = None
        self.is_outdated: bool = True

        self.recompute_need_and_available()

    def recompute_need_and_available(self) -> None:
        """Safely recomputes Need and Available vectors based on current data."""
        try:
            self.need = calculate_need(self.allocation, self.maximum)
        except Exception:
            self.need = [[0] * self.m for _ in range(self.n)]

        try:
            self.available = calculate_available(self.total, self.allocation)
        except Exception:
            self.available = [0] * self.m

    def mark_outdated(self) -> None:
        """Marks current algorithm results as outdated whenever inputs change."""
        self.is_outdated = True
        self.recompute_need_and_available()

    def check_data_loss_on_resize(self, new_n: int, new_m: int) -> Tuple[bool, str]:
        """
        Checks if shrinking dimensions will discard non-zero user data.
        Returns (has_data_loss, description_of_lost_data).
        """
        lost_details = []
        if new_n < self.n:
            for i in range(new_n, self.n):
                p_name = self.process_names[i]
                alloc_sum = sum(self.allocation[i])
                max_sum = sum(self.maximum[i])
                if alloc_sum > 0 or max_sum > 0:
                    lost_details.append(f"Process {p_name} (Allocated: {self.allocation[i]}, Max: {self.maximum[i]})")

        if new_m < self.m:
            for j in range(new_m, self.m):
                r_name = self.resource_names[j]
                tot = self.total[j]
                alloc_sum = sum(self.allocation[i][j] for i in range(min(new_n, self.n)))
                if tot > 0 or alloc_sum > 0:
                    lost_details.append(f"Resource {r_name} (Total: {tot}, Allocated: {alloc_sum})")

        if lost_details:
            msg = "Reducing dimensions will discard the following configured data:\n • " + "\n • ".join(lost_details)
            return True, msg
        return False, ""

    def resize(
        self,
        new_n: int,
        new_m: int,
        confirm_callback: Optional[Callable[[str], bool]] = None
    ) -> bool:
        """
        Resizes dimensions (n, m) dynamically while preserving ALL existing cells.
        If shrinking causes data loss and confirm_callback is provided, asks confirmation.
        """
        if new_n < 1 or new_m < 1:
            return False

        if new_n < self.n or new_m < self.m:
            has_loss, loss_msg = self.check_data_loss_on_resize(new_n, new_m)
            if has_loss and confirm_callback:
                confirmed = confirm_callback(loss_msg)
                if not confirmed:
                    return False

        old_n, old_m = self.n, self.m

        # Resize process names
        new_process_names = list(self.process_names[:new_n])
        for i in range(len(new_process_names), new_n):
            new_process_names.append(f"P{i}")

        # Resize resource names
        new_resource_names = list(self.resource_names[:new_m])
        for j in range(len(new_resource_names), new_m):
            letter = chr(65 + j) if j < 26 else f"R{j}"
            new_resource_names.append(letter)

        # Resize Total vector
        new_total = list(self.total[:new_m])
        for j in range(len(new_total), new_m):
            new_total.append(10)  # sensible default for new resource

        # Resize Allocation matrix
        new_allocation = []
        for i in range(new_n):
            row = []
            for j in range(new_m):
                if i < old_n and j < old_m:
                    row.append(self.allocation[i][j])
                else:
                    row.append(0)
            new_allocation.append(row)

        # Resize Maximum matrix
        new_maximum = []
        for i in range(new_n):
            row = []
            for j in range(new_m):
                if i < old_n and j < old_m:
                    row.append(self.maximum[i][j])
                else:
                    row.append(new_allocation[i][j])  # Need = 0 by default for new cells
            new_maximum.append(row)

        # Apply new state
        self.n = new_n
        self.m = new_m
        self.process_names = new_process_names
        self.resource_names = new_resource_names
        self.total = new_total
        self.allocation = new_allocation
        self.maximum = new_maximum

        self.mark_outdated()
        return True

    def add_process(self, name: Optional[str] = None) -> bool:
        """Adds a new process to the bottom of the matrices."""
        new_n = self.n + 1
        if new_n > 30:
            return False
        return self.resize(new_n, self.m)

    def remove_process(self, confirm_callback: Optional[Callable[[str], bool]] = None) -> bool:
        """Removes the last process if n > 1."""
        if self.n <= 1:
            return False
        return self.resize(self.n - 1, self.m, confirm_callback=confirm_callback)

    def add_resource(self, name: Optional[str] = None) -> bool:
        """Adds a new resource type column to the matrices."""
        new_m = self.m + 1
        if new_m > 15:
            return False
        return self.resize(self.n, new_m)

    def remove_resource(self, confirm_callback: Optional[Callable[[str], bool]] = None) -> bool:
        """Removes the last resource type column if m > 1."""
        if self.m <= 1:
            return False
        return self.resize(self.n, self.m - 1, confirm_callback=confirm_callback)

    def execute_safety_algorithm(self) -> Tuple[bool, Optional[str], Optional[SafetyResult]]:
        """
        Validates the scenario and runs the safety algorithm.
        Returns (success, error_message, SafetyResult).
        """
        valid, err = validate_scenario(
            total=self.total,
            allocation=self.allocation,
            maximum=self.maximum,
            process_names=self.process_names,
            resource_names=self.resource_names
        )
        if not valid:
            return False, err, None

        self.safety_result = run_safety_algorithm(
            total=self.total,
            allocation=self.allocation,
            maximum=self.maximum,
            process_names=self.process_names,
            resource_names=self.resource_names
        )
        self.is_outdated = False
        self.recompute_need_and_available()
        return True, None, self.safety_result

    def execute_request_simulation(
        self,
        process_index: int,
        request_vector: List[int]
    ) -> RequestResult:
        """
        Simulates a resource request and stores the result.
        """
        self.request_result = simulate_resource_request(
            total=self.total,
            allocation=self.allocation,
            maximum=self.maximum,
            process_index=process_index,
            request_vector=request_vector,
            process_names=self.process_names,
            resource_names=self.resource_names
        )
        return self.request_result

    def apply_granted_request(self) -> bool:
        """
        If the last simulated request was granted, updates the live scenario state.
        """
        if self.request_result and self.request_result.is_granted:
            self.allocation = copy.deepcopy(self.request_result.tentative_allocation)
            self.recompute_need_and_available()
            self.execute_safety_algorithm()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes scenario to dictionary for JSON persistence."""
        return {
            "title": self.title,
            "description": self.description,
            "n": self.n,
            "m": self.m,
            "process_names": list(self.process_names),
            "resource_names": list(self.resource_names),
            "total": list(self.total),
            "allocation": copy.deepcopy(self.allocation),
            "maximum": copy.deepcopy(self.maximum)
        }

    def save_to_json(self, filepath: str) -> None:
        """Saves scenario to a formatted JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    def load_from_json(self, filepath: str) -> None:
        """Loads scenario from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_from_dict(data)

    def export_to_csv(self, filepath: str) -> None:
        """Exports all matrices, Available, Need, and execution trace to a comprehensive CSV."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["BANKER'S ALGORITHM SIMULATOR - RESOURCE EXPORT"])
            writer.writerow(["Title", self.title])
            writer.writerow(["Processes (n)", self.n])
            writer.writerow(["Resource Types (m)", self.m])
            writer.writerow([])

            # Total & Available
            writer.writerow(["--- SYSTEM RESOURCE VECTORS ---"])
            writer.writerow(["Vector"] + self.resource_names)
            writer.writerow(["Total Instances"] + self.total)
            writer.writerow(["Initial Available"] + self.available)
            writer.writerow([])

            # Allocation Matrix
            writer.writerow(["--- ALLOCATION MATRIX ---"])
            writer.writerow(["Process"] + self.resource_names)
            for i in range(self.n):
                writer.writerow([self.process_names[i]] + self.allocation[i])
            writer.writerow([])

            # Maximum Demand Matrix
            writer.writerow(["--- MAXIMUM DEMAND MATRIX ---"])
            writer.writerow(["Process"] + self.resource_names)
            for i in range(self.n):
                writer.writerow([self.process_names[i]] + self.maximum[i])
            writer.writerow([])

            # Need Matrix
            writer.writerow(["--- NEED MATRIX (Maximum - Allocation) ---"])
            writer.writerow(["Process"] + self.resource_names)
            for i in range(self.n):
                writer.writerow([self.process_names[i]] + self.need[i])
            writer.writerow([])

            # Safety Result & Trace
            if self.safety_result:
                writer.writerow(["--- SAFETY ALGORITHM EXECUTION TRACE ---"])
                writer.writerow(["Status", "SAFE" if self.safety_result.is_safe else "UNSAFE"])
                if self.safety_result.is_safe:
                    writer.writerow(["Safe Sequence", " -> ".join(self.safety_result.safe_sequence)])
                else:
                    writer.writerow(["Unfinished Processes", ", ".join(self.safety_result.unfinished_processes)])
                writer.writerow([])
                writer.writerow([
                    "Step",
                    "Process",
                    "Work Before",
                    "Need",
                    "Allocation Released",
                    "Work After",
                    "Finish Vector"
                ])
                for step in self.safety_result.steps:
                    writer.writerow([
                        step.step_number,
                        step.process_name,
                        str(step.work_before),
                        str(step.need),
                        str(step.allocation),
                        str(step.work_after),
                        str(step.finish_status)
                    ])

    def generate_text_report(self) -> str:
        """Generates a detailed, student-friendly textual report with formatted tables."""
        lines = []
        lines.append("=" * 76)
        lines.append("   BANKER'S ALGORITHM SIMULATOR — OS RESOURCE MANAGEMENT REPORT")
        lines.append("=" * 76)
        lines.append(f"Scenario: {self.title}")
        lines.append(f"Configuration: {self.n} Processes, {self.m} Resource Types")
        lines.append("-" * 76)

        # Resources
        res_header = "  ".join(f"{r:>6}" for r in self.resource_names)
        tot_str = "  ".join(f"{v:>6}" for v in self.total)
        avail_str = "  ".join(f"{v:>6}" for v in self.available)
        lines.append(f"\nSystem Resources:\n  Name:       {res_header}\n  Total:      {tot_str}\n  Available:  {avail_str}\n")

        # Matrix Table
        lines.append("Process Matrices:")
        header_line = f"  {'Proc':<6} | " + f"{'Allocation':<{self.m*7}} | " + f"{'Maximum':<{self.m*7}} | " + f"{'Need':<{self.m*7}}"
        lines.append(header_line)
        lines.append("  " + "-" * (len(header_line) - 2))

        sub_header = f"  {'':<6} | " + " ".join(f"{r:>6}" for r in self.resource_names) + " | " + \
                     " ".join(f"{r:>6}" for r in self.resource_names) + " | " + \
                     " ".join(f"{r:>6}" for r in self.resource_names)
        lines.append(sub_header)
        lines.append("  " + "-" * (len(header_line) - 2))

        for i in range(self.n):
            alloc_s = " ".join(f"{v:>6}" for v in self.allocation[i])
            max_s = " ".join(f"{v:>6}" for v in self.maximum[i])
            need_s = " ".join(f"{v:>6}" for v in self.need[i])
            lines.append(f"  {self.process_names[i]:<6} | {alloc_s} | {max_s} | {need_s}")

        lines.append("  " + "-" * (len(header_line) - 2))

        # Results
        if self.safety_result:
            lines.append("\n" + "=" * 76)
            lines.append(f"RESULT: {self.safety_result.summary_title}")
            lines.append("=" * 76)
            lines.append(self.safety_result.summary_message)
            lines.append("")
            lines.append("Execution Trace:")
            for s in self.safety_result.steps:
                lines.append(f"  Step {s.step_number}: Process {s.process_name}")
                lines.append(f"    • Work Before: {s.work_before}")
                lines.append(f"    • Need:        {s.need} (≤ Work: True)")
                lines.append(f"    • Releasing:   {s.allocation}")
                lines.append(f"    • Work After:  {s.work_after}")
                lines.append(f"    • Finish:      {s.finish_status}")

            lines.append("\nEducational Note on Deadlock Avoidance:")
            lines.append(self.safety_result.educational_note)
        else:
            lines.append("\nSafety algorithm has not been executed yet on current configuration.")

        lines.append("\n" + "=" * 76)
        lines.append("End of Report.")
        lines.append("=" * 76)
        return "\n".join(lines)
