"""
Extended Tests — Check Details, Unfinished Details, Serialization
-----------------------------------------------------------------
Tests the new fields added to StepTrace and SafetyResult.
Extends the existing test suite without modifying it.
"""

import unittest
import json
from banker_algorithm import (
    calculate_need,
    calculate_available,
    run_safety_algorithm,
    simulate_resource_request,
    get_classic_safe_preset,
    get_classic_unsafe_preset,
    get_zero_need_preset,
    generate_random_valid_scenario,
    CheckDetail,
)
from validation import validate_scenario


class TestCheckDetails(unittest.TestCase):
    """Tests that the new per-resource check details are populated correctly."""

    def setUp(self):
        self.safe = get_classic_safe_preset()

    def test_checks_populated_on_safe(self):
        """Each step should have checks (list of lists of CheckDetail)."""
        result = run_safety_algorithm(
            self.safe["total"], self.safe["allocation"], self.safe["maximum"],
            self.safe["process_names"], self.safe["resource_names"]
        )
        self.assertTrue(result.is_safe)
        for step in result.steps:
            self.assertIsInstance(step.checks, list)
            self.assertGreater(len(step.checks), 0, f"Step {step.step_number} has no checks")
            # The last checked process in each step should be the selected one
            last_checks = step.checks[-1]
            self.assertEqual(last_checks[0].process_name, step.process_name)
            # All checks for the selected process should be satisfied
            self.assertTrue(all(c.satisfied for c in last_checks))

    def test_skipped_processes_recorded(self):
        """Step 1 selects P1. P0 should have been checked and skipped before P1."""
        result = run_safety_algorithm(
            self.safe["total"], self.safe["allocation"], self.safe["maximum"],
            self.safe["process_names"], self.safe["resource_names"]
        )
        step1 = result.steps[0]
        # P0 should be in skipped (Need [7,4,3] > Work [3,3,2])
        self.assertGreater(len(step1.skipped_processes), 0)
        skip_names = [s["process_name"] for s in step1.skipped_processes]
        self.assertIn("P0", skip_names)
        # P0 skip should have shortage info
        p0_skip = next(s for s in step1.skipped_processes if s["process_name"] == "P0")
        self.assertIn("shortage", p0_skip)
        self.assertGreater(len(p0_skip["shortage"]), 0)

    def test_check_detail_fields(self):
        """CheckDetail has correct field values for a known comparison."""
        result = run_safety_algorithm(
            self.safe["total"], self.safe["allocation"], self.safe["maximum"],
            self.safe["process_names"], self.safe["resource_names"]
        )
        # Step 1 checks P0 first. P0 Need for resource A is 7, Work A is 3.
        step1 = result.steps[0]
        p0_checks = step1.checks[0]  # First process checked
        self.assertEqual(p0_checks[0].process_name, "P0")
        self.assertEqual(p0_checks[0].resource_name, "A")
        self.assertEqual(p0_checks[0].need_value, 7)
        self.assertEqual(p0_checks[0].work_value, 3)
        self.assertFalse(p0_checks[0].satisfied)


class TestUnfinishedDetails(unittest.TestCase):
    """Tests the unfinished_details field for unsafe states."""

    def setUp(self):
        self.unsafe = get_classic_unsafe_preset()

    def test_unfinished_details_populated(self):
        """Unsafe result should have unfinished_details with shortage info."""
        result = run_safety_algorithm(
            self.unsafe["total"], self.unsafe["allocation"], self.unsafe["maximum"],
            self.unsafe["process_names"], self.unsafe["resource_names"]
        )
        self.assertFalse(result.is_safe)
        self.assertGreater(len(result.unfinished_details), 0)
        for detail in result.unfinished_details:
            self.assertIn("process_name", detail)
            self.assertIn("shortage", detail)
            self.assertIn("waiting_for", detail)
            self.assertIsInstance(detail["waiting_for"], list)
            self.assertGreater(len(detail["waiting_for"]), 0)

    def test_unfinished_details_empty_when_safe(self):
        """Safe result should have empty unfinished_details."""
        safe = get_classic_safe_preset()
        result = run_safety_algorithm(
            safe["total"], safe["allocation"], safe["maximum"],
            safe["process_names"], safe["resource_names"]
        )
        self.assertTrue(result.is_safe)
        self.assertEqual(result.unfinished_details, [])


class TestSerializable(unittest.TestCase):
    """Tests that all result objects can be serialized to JSON for the API."""

    def _to_dict(self, result):
        """Convert SafetyResult to a JSON-serializable dict."""
        steps_data = []
        for s in result.steps:
            checks_data = []
            for proc_checks in s.checks:
                checks_data.append([{
                    "process_name": c.process_name,
                    "resource_name": c.resource_name,
                    "need_value": c.need_value,
                    "work_value": c.work_value,
                    "satisfied": c.satisfied
                } for c in proc_checks])
            steps_data.append({
                "step_number": s.step_number,
                "process_name": s.process_name,
                "work_before": s.work_before,
                "need": s.need,
                "allocation": s.allocation,
                "work_after": s.work_after,
                "finish_status": s.finish_status,
                "checks": checks_data,
                "skipped_processes": s.skipped_processes,
            })
        return {
            "is_safe": result.is_safe,
            "safe_sequence": result.safe_sequence,
            "unfinished_processes": result.unfinished_processes,
            "unfinished_details": result.unfinished_details,
            "steps": steps_data,
            "initial_available": result.initial_available,
            "final_work": result.final_work,
        }

    def test_safe_result_serializable(self):
        safe = get_classic_safe_preset()
        result = run_safety_algorithm(
            safe["total"], safe["allocation"], safe["maximum"],
            safe["process_names"], safe["resource_names"]
        )
        d = self._to_dict(result)
        s = json.dumps(d)
        parsed = json.loads(s)
        self.assertTrue(parsed["is_safe"])
        self.assertEqual(len(parsed["steps"]), 5)

    def test_unsafe_result_serializable(self):
        unsafe = get_classic_unsafe_preset()
        result = run_safety_algorithm(
            unsafe["total"], unsafe["allocation"], unsafe["maximum"],
            unsafe["process_names"], unsafe["resource_names"]
        )
        d = self._to_dict(result)
        s = json.dumps(d)
        parsed = json.loads(s)
        self.assertFalse(parsed["is_safe"])
        self.assertGreater(len(parsed["unfinished_details"]), 0)


class TestMultipleProcessCounts(unittest.TestCase):
    """Tests the algorithm with various dynamic sizes to ensure no hardcoding."""

    def test_sizes_1_to_10(self):
        """Run random scenarios from 1x1 to 10x5 and verify results are valid."""
        for n in range(1, 11):
            m = min(n, 5)
            scenario = generate_random_valid_scenario(n, m)
            valid, err = validate_scenario(
                scenario["total"], scenario["allocation"], scenario["maximum"],
                scenario["process_names"], scenario["resource_names"]
            )
            self.assertTrue(valid, f"n={n} m={m} failed validation: {err}")
            result = run_safety_algorithm(
                scenario["total"], scenario["allocation"], scenario["maximum"],
                scenario["process_names"], scenario["resource_names"]
            )
            # Every process should be in either safe_sequence or unfinished
            total_accounted = len(result.safe_sequence) + len(result.unfinished_processes)
            self.assertEqual(total_accounted, n,
                             f"n={n}: accounted {total_accounted} processes")
            # Final work should equal total when safe
            if result.is_safe:
                self.assertEqual(result.final_work, scenario["total"])


if __name__ == "__main__":
    unittest.main()
