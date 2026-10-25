"""
Acceptance Tests for Dynamic Configuration & Data Preservation
--------------------------------------------------------------
Tests the dynamic resizing, data preservation on expansion,
confirmation hooks on shrinking with data loss, and execution
across arbitrary dimensions (3x2 -> 7x4 -> 2x1).
"""

import unittest
from scenario_manager import ScenarioManager
from banker_algorithm import run_safety_algorithm


class TestDynamicConfiguration(unittest.TestCase):

    def test_dynamic_flow_3x2_to_7x4_to_2x1(self):
        """
        Acceptance Test:
        1. Start with 3 processes and 2 resources.
        2. Enter custom values.
        3. Expand to 7 processes and 4 resources -> verify old values preserved.
        4. Reduce to 2 processes and 1 resource -> verify shrinking and callback.
        5. Verify algorithm runs properly without crashes.
        """
        # Step 1: Start with 3 processes, 2 resources
        mgr = ScenarioManager()
        self.assertTrue(mgr.resize(3, 2))
        self.assertEqual(mgr.n, 3)
        self.assertEqual(mgr.m, 2)
        self.assertEqual(len(mgr.allocation), 3)
        self.assertEqual(len(mgr.allocation[0]), 2)

        # Set custom test data
        mgr.total = [12, 10]
        mgr.allocation[0] = [2, 1]
        mgr.maximum[0] = [4, 3]
        mgr.allocation[1] = [3, 2]
        mgr.maximum[1] = [5, 4]
        mgr.allocation[2] = [1, 1]
        mgr.maximum[2] = [2, 2]
        mgr.recompute_need_and_available()

        # Available = [12 - (2+3+1), 10 - (1+2+1)] = [12 - 6, 10 - 4] = [6, 6]
        self.assertEqual(mgr.available, [6, 6])
        self.assertEqual(mgr.need[0], [2, 2])

        # Step 2: Expand to 7 processes and 4 resources
        self.assertTrue(mgr.resize(7, 4))
        self.assertEqual(mgr.n, 7)
        self.assertEqual(mgr.m, 4)

        # Step 3: Verify existing data preserved!
        self.assertEqual(mgr.allocation[0][:2], [2, 1])
        self.assertEqual(mgr.maximum[0][:2], [4, 3])
        self.assertEqual(mgr.allocation[1][:2], [3, 2])
        self.assertEqual(mgr.maximum[1][:2], [5, 4])
        self.assertEqual(mgr.allocation[2][:2], [1, 1])
        self.assertEqual(mgr.maximum[2][:2], [2, 2])
        # Verify new cells are initialized cleanly
        self.assertEqual(mgr.allocation[6], [0, 0, 0, 0])

        # Step 4: Verify data loss detection when shrinking
        has_loss, loss_msg = mgr.check_data_loss_on_resize(2, 1)
        self.assertTrue(has_loss)
        self.assertIn("Process", loss_msg)

        # Reject shrinking if callback returns False
        rejected = mgr.resize(2, 1, confirm_callback=lambda msg: False)
        self.assertFalse(rejected)
        self.assertEqual(mgr.n, 7)  # Dimensions should remain 7x4

        # Accept shrinking if callback returns True
        accepted = mgr.resize(2, 1, confirm_callback=lambda msg: True)
        self.assertTrue(accepted)
        self.assertEqual(mgr.n, 2)
        self.assertEqual(mgr.m, 1)

        # Values in top-left (P0, P1 on resource A) must still be preserved!
        self.assertEqual(mgr.allocation[0], [2])
        self.assertEqual(mgr.maximum[0], [4])
        self.assertEqual(mgr.allocation[1], [3])
        self.assertEqual(mgr.maximum[1], [5])

        # Step 5: Run safety algorithm on 2x1 configuration
        ok, err, safety_res = mgr.execute_safety_algorithm()
        self.assertTrue(ok)
        self.assertIsNotNone(safety_res)
        self.assertEqual(len(safety_res.safe_sequence) + len(safety_res.unfinished_processes), 2)

    def test_json_and_csv_export(self):
        """Test exporting scenario to JSON, reloading it, and exporting report."""
        mgr = ScenarioManager()
        data_dict = mgr.to_dict()
        self.assertEqual(data_dict["n"], 5)
        self.assertEqual(data_dict["m"], 3)

        report = mgr.generate_text_report()
        self.assertIn("BANKER'S ALGORITHM SIMULATOR", report)
        self.assertIn("Allocation", report)
        self.assertIn("Need", report)


if __name__ == "__main__":
    unittest.main()
