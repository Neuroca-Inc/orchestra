import tempfile
import unittest
from pathlib import Path

from phase_tracker.discovery import compute_target, scan_project
from phase_tracker.domain import ArchiveAction, Coordinate


class DiscoveryTests(unittest.TestCase):
    def test_scans_descriptive_phase_and_computes_all_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            phase = root / "Phase-5_Prime_QBL"
            (phase / "p5-b1" / "p5-b1-v1").mkdir(parents=True)
            (phase / "p5-b1" / "p5-b1-v2").mkdir()
            (phase / "p5-b3" / "p5-b3-v10").mkdir(parents=True)

            index = scan_project(root)
            current = Coordinate(5, 3, 10, "Phase-5_Prime_QBL")

            continued = compute_target(index, ArchiveAction.CONTINUE, current)
            new_branch = compute_target(index, ArchiveAction.NEW_BRANCH, current)
            new_phase = compute_target(index, ArchiveAction.NEW_PHASE, current)

            self.assertEqual(
                continued.coordinate.relative_path(),
                Path("Phase-5_Prime_QBL/p5-b3/p5-b3-v11"),
            )
            self.assertEqual(
                new_branch.coordinate.relative_path(),
                Path("Phase-5_Prime_QBL/p5-b4/p5-b4-v1"),
            )
            self.assertEqual(
                new_phase.coordinate.relative_path(),
                Path("p6/p6-b1/p6-b1-v1"),
            )

    def test_empty_project_starts_at_p1_b1_v1(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = compute_target(scan_project(root), ArchiveAction.CONTINUE, None)
            self.assertEqual(target.coordinate.relative_path(), Path("p1/p1-b1/p1-b1-v1"))

    def test_duplicate_phase_numbers_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "p5").mkdir()
            (root / "Phase-5_Prime_QBL").mkdir()
            with self.assertRaisesRegex(ValueError, "Ambiguous phase directories"):
                compute_target(scan_project(root), ArchiveAction.NEW_PHASE, None)


    def test_descriptive_version_names_are_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            branch = root / "p1" / "p1-b1"
            (branch / "p1-b1-v4").mkdir(parents=True)
            descriptive = branch / "p1-b1-v18_barrier-renewal-ladder_20260908_002100"
            descriptive.mkdir()

            index = scan_project(root)
            current = index.coordinate_for(1, 1)

            self.assertEqual(current.version, 18)
            self.assertEqual(
                index.phases[1].branches[1].version_paths[18], descriptive
            )
            continued = compute_target(index, ArchiveAction.CONTINUE, current)
            self.assertEqual(continued.coordinate.version, 19)
            self.assertEqual(continued.version_path.name, "p1-b1-v19")

    def test_project_can_start_from_non_v1_descriptive_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            descriptive = (
                root / "p7" / "p7-b3" /
                "p7-b3-v22_existing-provenance-package_20260908"
            )
            descriptive.mkdir(parents=True)

            index = scan_project(root)
            current = index.latest_coordinate()

            self.assertIsNotNone(current)
            self.assertEqual((current.phase, current.branch, current.version), (7, 3, 22))
            self.assertEqual(
                index.phases[7].branches[3].version_paths[22], descriptive
            )


if __name__ == "__main__":
    unittest.main()

