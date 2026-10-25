"""
Comprehensive Unit Tests for Banker's Algorithm Simulator
---------------------------------------------------------
Covers:
- Need and Available calculations
- Known safe example (Silberschatz 5x3)
- Known unsafe example
- Validation of invalid matrices and over-allocations
- Process with zero additional need
- Resource request granted
- Resource request denied (Request > Need)
- Resource request denied (Request > Available)
- Resource request denied (Tentative state unsafe with rollback)
- Single process, single resource edge case
- Presets and random generator sanity checks
"""

import unittest
from banker_algorithm import (
    calculate_need,
    calculate_available,
    run_safety_algorithm,
    simulate_resource_request,
    get_classic_safe_preset,
    get_classic_unsafe_preset,
    get_zero_need_preset,
    generate_random_valid_scenario
)
from validation import validate_scenario, validate_dimensions, validate_names, validate_request


class TestBankerAlgorithm(unittest.TestCase):

    def setUp(self):
        self.safe_preset = get_classic_safe_preset()
        self.unsafe_preset = get_classic_unsafe_preset()

    def test_need_calculation(self):
        """Test calculation of Need matrix: Need = Max - Alloc."""
        alloc = [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2]
        ]
        max_mat = [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2]
        ]
        expected_need = [
            [7, 4, 3],
            [1, 2, 2],
            [6, 0, 0]
        ]
        calculated = calculate_need(alloc, max_mat)
        self.assertEqual(calculated, expected_need)

    def test_available_calculation(self):
        """Test calculation of Available vector: Available = Total - sum(Alloc)."""
        total = [10, 5, 7]
        alloc = [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2]
        ]
        # Sum alloc: [7, 2, 5]
        # Available: [10-7, 5-2, 7-5] = [3, 3, 2]
        available = calculate_available(total, alloc)
        self.assertEqual(available, [3, 3, 2])

    def test_known_safe_scenario(self):
        """Test classic Silberschatz 5x3 safe example."""
        result = run_safety_algorithm(
            total=self.safe_preset["total"],
            allocation=self.safe_preset["allocation"],
            maximum=self.safe_preset["maximum"],
            process_names=self.safe_preset["process_names"],
            resource_names=self.safe_preset["resource_names"]
        )
        self.assertTrue(result.is_safe)
        self.assertEqual(len(result.safe_sequence), 5)
        self.assertEqual(result.unfinished_processes, [])
        # P1 is satisfied first in canonical search because Need[P1] = [1, 2, 2] <= Available [3, 3, 2]
        self.assertEqual(result.safe_sequence[0], "P1")
        # Final work should equal total resources when all processes finish
        self.assertEqual(result.final_work, self.safe_preset["total"])

    def test_known_unsafe_scenario(self):
        """Test unsafe scenario where no process can proceed."""
        result = run_safety_algorithm(
            total=self.unsafe_preset["total"],
            allocation=self.unsafe_preset["allocation"],
            maximum=self.unsafe_preset["maximum"],
            process_names=self.unsafe_preset["process_names"],
            resource_names=self.unsafe_preset["resource_names"]
        )
        self.assertFalse(result.is_safe)
        self.assertGreater(len(result.unfinished_processes), 0)
        self.assertIn("UNSAFE STATE", result.summary_title)
        self.assertIn("CRITICAL OPERATING SYSTEMS CONCEPT", result.educational_note)

    def test_zero_need_process(self):
        """Test edge case where a process needs zero additional resources."""
        preset = get_zero_need_preset()
        result = run_safety_algorithm(
            total=preset["total"],
            allocation=preset["allocation"],
            maximum=preset["maximum"],
            process_names=preset["process_names"],
            resource_names=preset["resource_names"]
        )
        self.assertTrue(result.is_safe)
        # P1 has Need = [0, 0], so it should satisfy condition immediately
        self.assertIn("P1", result.safe_sequence)

    def test_single_process_single_resource(self):
        """Edge case: 1 process, 1 resource type."""
        total = [5]
        alloc = [[2]]
        max_mat = [[5]]
        result = run_safety_algorithm(total, alloc, max_mat, ["P0"], ["R0"])
        self.assertTrue(result.is_safe)
        self.assertEqual(result.safe_sequence, ["P0"])
        self.assertEqual(result.final_work, [5])

    def test_request_granted(self):
        """
        In classic Silberschatz, if P1 requests [1, 0, 2]:
        Need[P1] is [1, 2, 2] -> [1, 0, 2] <= [1, 2, 2] (OK)
        Available is [3, 3, 2] -> [1, 0, 2] <= [3, 3, 2] (OK)
        Tentative Available: [2, 3, 0]
        Tentative Alloc[P1]: [3, 0, 2]
        Tentative Need[P1]: [0, 2, 0]
        Safe sequence exists (e.g. P1 -> P3 -> P4 -> P0 -> P2). Request must be GRANTED.
        """
        req_res = simulate_resource_request(
            total=self.safe_preset["total"],
            allocation=self.safe_preset["allocation"],
            maximum=self.safe_preset["maximum"],
            process_index=1,
            request_vector=[1, 0, 2],
            process_names=self.safe_preset["process_names"],
            resource_names=self.safe_preset["resource_names"]
        )
        self.assertTrue(req_res.is_granted)
        self.assertIsNone(req_res.rejection_stage)
        self.assertTrue(req_res.safety_result.is_safe)
        self.assertEqual(req_res.tentative_available, [2, 3, 0])

    def test_request_denied_exceeds_need(self):
        """Request denied if Request > Need (Stage 1)."""
        # P1 Need is [1, 2, 2]. Request [2, 0, 0] exceeds resource A need.
        req_res = simulate_resource_request(
            total=self.safe_preset["total"],
            allocation=self.safe_preset["allocation"],
            maximum=self.safe_preset["maximum"],
            process_index=1,
            request_vector=[2, 0, 0],
            process_names=self.safe_preset["process_names"],
            resource_names=self.safe_preset["resource_names"]
        )
        self.assertFalse(req_res.is_granted)
        self.assertEqual(req_res.rejection_stage, 1)
        self.assertIn("exceeds its declared remaining Need", req_res.rejection_reason)

    def test_request_denied_exceeds_available(self):
        """Request denied if Request > Available (Stage 2)."""
        # P0 Need is [7, 4, 3]. Available is [3, 3, 2].
        # P0 requests [0, 2, 0] -> Need ok, but if P0 requests [0, 4, 0] -> Available of B is only 3.
        # Wait, P0 Need for B is 4. Request [0, 4, 0] is <= Need (4), but > Available (3).
        req_res = simulate_resource_request(
            total=self.safe_preset["total"],
            allocation=self.safe_preset["allocation"],
            maximum=self.safe_preset["maximum"],
            process_index=0,
            request_vector=[0, 4, 0],
            process_names=self.safe_preset["process_names"],
            resource_names=self.safe_preset["resource_names"]
        )
        self.assertFalse(req_res.is_granted)
        self.assertEqual(req_res.rejection_stage, 2)
        self.assertIn("Process must wait", req_res.rejection_reason)

    def test_request_denied_unsafe_state_rollback(self):
        """
        Request is <= Need and <= Available, but tentative allocation causes an unsafe state (Stage 3).
        Original state must be preserved and change rolled back.
        """
        # In Silberschatz: If P0 requests [0, 2, 0]:
        # Need[P0] is [7, 4, 3], Available is [3, 3, 2]. [0, 2, 0] is <= Need and <= Available.
        # Tentative Available becomes [3, 1, 2].
        # Let's see if P0 requests [3, 3, 0]:
        # Available becomes [0, 0, 2]. Can any process proceed?
        # Need[P1] is [1, 2, 2] > [0, 0, 2] (cannot proceed).
        # Need[P3] is [0, 1, 1] > [0, 0, 2] (cannot proceed, needs 1 of B).
        # All processes blocked! Unsafe!
        # P0 Need is [7, 4, 3], so [3, 3, 0] <= Need and <= Available [3, 3, 2].
        req_res = simulate_resource_request(
            total=self.safe_preset["total"],
            allocation=self.safe_preset["allocation"],
            maximum=self.safe_preset["maximum"],
            process_index=0,
            request_vector=[3, 3, 0],
            process_names=self.safe_preset["process_names"],
            resource_names=self.safe_preset["resource_names"]
        )
        self.assertFalse(req_res.is_granted)
        self.assertEqual(req_res.rejection_stage, 3)
        self.assertIn("ROLLED BACK", req_res.explanation)
        self.assertFalse(req_res.safety_result.is_safe)
        # Ensure original matrices remained intact
        self.assertEqual(req_res.original_allocation, self.safe_preset["allocation"])

    def test_random_scenario_validity(self):
        """Ensure randomly generated scenarios are always logically valid."""
        for _ in range(5):
            scenario = generate_random_valid_scenario(n=4, m=3)
            valid, err = validate_scenario(
                total=scenario["total"],
                allocation=scenario["allocation"],
                maximum=scenario["maximum"],
                process_names=scenario["process_names"],
                resource_names=scenario["resource_names"]
            )
            self.assertTrue(valid, f"Random scenario failed validation: {err}")


class TestValidation(unittest.TestCase):

    def test_valid_scenario_passes(self):
        safe_preset = get_classic_safe_preset()
        valid, err = validate_scenario(
            total=safe_preset["total"],
            allocation=safe_preset["allocation"],
            maximum=safe_preset["maximum"],
            process_names=safe_preset["process_names"],
            resource_names=safe_preset["resource_names"]
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_allocation_greater_than_maximum(self):
        """Reject if Allocation[i][j] > Maximum[i][j]."""
        total = [10, 10]
        alloc = [[5, 3]]
        max_mat = [[4, 3]]  # 4 < 5 for resource A!
        valid, err = validate_scenario(total, alloc, max_mat, ["P0"], ["A", "B"])
        self.assertFalse(valid)
        self.assertIn("Maximum demand (4) cannot be less than current allocation (5)", err)

    def test_sum_allocation_greater_than_total(self):
        """Reject if sum(Allocation) > Total."""
        total = [5, 5]
        alloc = [
            [3, 2],
            [3, 1]  # Sum A is 3+3=6 > 5
        ]
        max_mat = [
            [4, 4],
            [4, 4]
        ]
        valid, err = validate_scenario(total, alloc, max_mat)
        self.assertFalse(valid)
        self.assertIn("exceeds the total system capacity", err)

    def test_negative_values(self):
        """Reject negative integers."""
        total = [5, -2]
        alloc = [[1, 0]]
        max_mat = [[2, 0]]
        valid, err = validate_scenario(total, alloc, max_mat)
        self.assertFalse(valid)
        self.assertIn("must be a non-negative integer", err)

    def test_dimension_validation(self):
        self.assertFalse(validate_dimensions(0, 3)[0])
        self.assertFalse(validate_dimensions(3, 0)[0])
        self.assertTrue(validate_dimensions(5, 3)[0])

    def test_names_validation(self):
        self.assertFalse(validate_names(["P0", "P0"], ["A", "B"], 2, 2)[0])  # Duplicate
        self.assertFalse(validate_names(["P0", ""], ["A", "B"], 2, 2)[0])    # Empty
        self.assertTrue(validate_names(["P0", "P1"], ["A", "B"], 2, 2)[0])


if __name__ == "__main__":
    unittest.main()
