"""
GUI Integration and Interactive Component Tests
------------------------------------------------
Tests the GUI widgets, stepper playback transitions,
table rebuilds on dynamic resizing, and request tester logic.
"""

import unittest
from unittest.mock import patch
import os
import tempfile
import tkinter as tk
from gui import BankersSimulatorApp


class TestGUIIntegration(unittest.TestCase):

    def setUp(self):
        os.environ["TK_SILENCE_DEPRECATION"] = "1"
        self.app = BankersSimulatorApp()
        self.app.update_idletasks()

    def tearDown(self):
        if self.app:
            self.app.destroy()

    def test_initial_state_and_cards(self):
        """Verifies initial cards display 5 processes, 3 types, and SAFE STATE."""
        self.assertEqual(self.app.card_n.cget("text"), "5 Processes")
        self.assertEqual(self.app.card_m.cget("text"), "3 Types")
        self.assertEqual(self.app.card_status.cget("text"), "SAFE STATE")
        self.assertEqual(self.app.card_avail.cget("text"), "[3, 3, 2]")

    @patch("tkinter.messagebox.askyesno", return_value=True)
    def test_dynamic_dimension_change(self, mock_ask):
        """Tests changing dimensions dynamically via spinboxes and on_apply_dimensions."""
        self.app.spin_n.delete(0, tk.END)
        self.app.spin_n.insert(0, "4")
        self.app.spin_m.delete(0, tk.END)
        self.app.spin_m.insert(0, "2")
        self.app.on_apply_dimensions()
        self.app.update_idletasks()

        self.assertEqual(self.app.mgr.n, 4)
        self.assertEqual(self.app.mgr.m, 2)
        self.assertEqual(self.app.card_n.cget("text"), "4 Processes")
        self.assertEqual(self.app.card_m.cget("text"), "2 Types")

    def test_stepper_playback_and_safe_sequence(self):
        """Tests the simulation stepper forward, backward, and safe sequence accumulation."""
        stepper = self.app.sim_stepper
        self.assertIsNotNone(stepper.safety_result)

        # Initially at step -1 (start)
        self.assertEqual(stepper.current_step_idx, -1)

        # Step forward
        stepper.go_next()
        self.assertEqual(stepper.current_step_idx, 0)
        self.assertEqual(stepper.safety_result.steps[0].process_name, "P1")

        # Step to last
        stepper.go_last()
        self.assertEqual(stepper.current_step_idx, len(stepper.safety_result.steps) - 1)

        # Step backward
        stepper.go_prev()
        self.assertEqual(stepper.current_step_idx, len(stepper.safety_result.steps) - 2)

        # Reset
        stepper.reset_sim()
        self.assertEqual(stepper.current_step_idx, -1)

    def test_request_tester_interaction(self):
        """Tests interacting with request tester widget."""
        req_tester = self.app.request_tester
        req_tester.proc_var.set("P1")
        req_tester._on_proc_selected()

        # Set request entries to [1, 0, 2]
        for ent, val in zip(req_tester.request_entries, ["1", "0", "2"]):
            ent.delete(0, tk.END)
            ent.insert(0, val)

        req_tester.evaluate_request()
        self.assertIsNotNone(req_tester.last_result)
        self.assertTrue(req_tester.last_result.is_granted)
        self.assertIn("APPROVED", req_tester.lbl_decision_banner.cget("text"))

    def test_csv_and_report_export(self):
        """Verifies CSV and text export generate non-empty valid files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test_export.csv")
            rep_path = os.path.join(tmpdir, "test_report.txt")

            self.app.mgr.export_to_csv(csv_path)
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("BANKER'S ALGORITHM", content)
                self.assertIn("ALLOCATION MATRIX", content)

            with open(rep_path, "w", encoding="utf-8") as f:
                f.write(self.app.mgr.generate_text_report())
            self.assertTrue(os.path.exists(rep_path))
            with open(rep_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("SYSTEM IS IN A SAFE STATE", content)


if __name__ == "__main__":
    unittest.main()
