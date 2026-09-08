import json
import tempfile
import unittest
from pathlib import Path

from phase_tracker.archive import ArchiveError, ArchiveService
from phase_tracker.domain import ArchiveAction, WorkflowMode, WorkflowState
from phase_tracker.state_store import StateStore


class OperatorSkirmishTests(unittest.TestCase):
    def test_bootstrap_creates_first_version_and_keeps_operator_active(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
            receipt = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                None,
                state,
                "Pass sealed",
                [],
                "# Skirmish v1\n\nSealed.",
            )
            self.assertEqual(
                receipt.coordinate.relative_path(),
                Path("p1/p1-b1/p1-b1-v1"),
            )
            self.assertTrue(receipt.created_coordinate)
            self.assertEqual(
                receipt.next_state.workflow_mode,
                WorkflowMode.OPERATOR_SKIRMISH,
            )
            manifest = json.loads(
                (receipt.destination / "p1-b1-v1-archive.json").read_text()
            )
            self.assertEqual(manifest["workflow_mode"], "operator_skirmish")
            self.assertEqual(manifest["source_agent"], "Operator")
            self.assertEqual(manifest["next_agent"], "Operator")
            self.assertEqual(manifest["coordinate_authority"], "STRUCTURAL BOOTSTRAP")

    def test_sealed_continue_advances_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
            first = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                None,
                state,
                "Pass sealed",
                [],
                "v1",
            )
            second = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                first.coordinate,
                first.next_state,
                "Pass sealed",
                [],
                "v2",
            )
            self.assertEqual(
                second.coordinate.relative_path(),
                Path("p1/p1-b1/p1-b1-v2"),
            )
            self.assertTrue(second.created_coordinate)
            manifest = json.loads(
                (second.destination / "p1-b1-v2-archive.json").read_text()
            )
            self.assertEqual(
                manifest["coordinate_authority"],
                "OPERATOR SKIRMISH PASS",
            )

    def test_not_sealed_appends_to_current_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
            first = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                None,
                state,
                "Pass sealed",
                [],
                "v1",
            )
            open_pass = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                first.coordinate,
                first.next_state,
                "Not sealed",
                [],
                "more work required",
            )
            self.assertFalse(open_pass.created_coordinate)
            self.assertEqual(open_pass.destination, first.destination)
            self.assertFalse((root / "p1" / "p1-b1" / "p1-b1-v2").exists())

    def test_unsealed_pass_cannot_create_branch_or_phase(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
            first = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                None,
                state,
                "Pass sealed",
                [],
                "v1",
            )
            for action in (ArchiveAction.NEW_BRANCH, ArchiveAction.NEW_PHASE):
                with self.subTest(action=action):
                    with self.assertRaisesRegex(ArchiveError, "sealed Operator Skirmish"):
                        ArchiveService().record(
                            root,
                            action,
                            first.coordinate,
                            first.next_state,
                            "Not sealed",
                            [],
                            "still open",
                        )

    def test_sealed_pass_can_create_new_branch_and_phase(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
            first = ArchiveService().record(
                root,
                ArchiveAction.CONTINUE,
                None,
                state,
                "Pass sealed",
                [],
                "v1",
            )
            branch = ArchiveService().record(
                root,
                ArchiveAction.NEW_BRANCH,
                first.coordinate,
                first.next_state,
                "Pass sealed",
                [],
                "new branch",
            )
            self.assertEqual(
                branch.coordinate.relative_path(),
                Path("p1/p1-b2/p1-b2-v1"),
            )
            phase = ArchiveService().record(
                root,
                ArchiveAction.NEW_PHASE,
                branch.coordinate,
                branch.next_state,
                "Pass sealed",
                [],
                "new phase",
            )
            self.assertEqual(
                phase.coordinate.relative_path(),
                Path("p2/p2-b1/p2-b1-v1"),
            )

    def test_state_round_trip_preserves_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
            store = StateStore(root)
            store.save(state)
            loaded = store.load()
            self.assertEqual(loaded.workflow_mode, WorkflowMode.OPERATOR_SKIRMISH)


if __name__ == "__main__":
    unittest.main()
