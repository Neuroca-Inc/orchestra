import unittest

from phase_tracker.domain import (
    Agent,
    ProjectStatus,
    WorkflowMode,
    WorkflowState,
)
from phase_tracker.workflow import (
    WORKFLOW_POSITIONS,
    advance,
    align_mode,
    align_position,
    describe_position,
    workflow_positions,
)


class WorkflowTests(unittest.TestCase):
    def test_operator_guardian_auditor_guardian_cycle(self) -> None:
        state = WorkflowState()

        operator = advance(state, "Package produced")
        self.assertEqual(operator.next_state.active_agent, Agent.GUARDIAN)
        self.assertEqual(operator.next_state.guardian_subject, Agent.OPERATOR)

        guardian_operator = advance(operator.next_state, "Pass")
        self.assertEqual(guardian_operator.next_state.active_agent, Agent.AUDITOR)
        self.assertIsNone(guardian_operator.next_state.guardian_subject)
        self.assertIn("ratification", guardian_operator.handoff)

        auditor = advance(guardian_operator.next_state, "Fail")
        self.assertEqual(auditor.next_state.active_agent, Agent.GUARDIAN)
        self.assertEqual(auditor.next_state.guardian_subject, Agent.AUDITOR)

        guardian_auditor = advance(auditor.next_state, "Fail")
        self.assertEqual(guardian_auditor.next_state.active_agent, Agent.AUDITOR)
        self.assertIsNone(guardian_auditor.next_state.guardian_subject)
        self.assertTrue(guardian_auditor.next_state.auditor_revision)

        revised_auditor = advance(guardian_auditor.next_state, "Pass")
        self.assertTrue(revised_auditor.next_state.auditor_revision)
        guardian_rejects_revision = advance(revised_auditor.next_state, "Fail")
        self.assertTrue(guardian_rejects_revision.next_state.auditor_revision)
        revised_again = advance(guardian_rejects_revision.next_state, "Fail")
        self.assertTrue(revised_again.next_state.auditor_revision)
        guardian_accepts_revision = advance(revised_auditor.next_state, "Pass")
        self.assertEqual(
            guardian_accepts_revision.next_state.active_agent, Agent.OPERATOR
        )
        self.assertFalse(
            guardian_accepts_revision.next_state.auditor_revision
        )

    def test_not_produced_repeats_operator(self) -> None:
        transition = advance(WorkflowState(), "Not produced")
        self.assertEqual(transition.next_state.active_agent, Agent.OPERATOR)
        self.assertIsNone(transition.next_state.guardian_subject)

    def test_complete_closes_project(self) -> None:
        transition = advance(WorkflowState(), "Project complete")
        self.assertEqual(transition.next_state.status, ProjectStatus.COMPLETE)

    def test_manual_alignment_can_start_at_auditor(self) -> None:
        state = align_position(WorkflowState(), "Auditor")
        self.assertEqual(state.active_agent, Agent.AUDITOR)
        self.assertIsNone(state.guardian_subject)
        self.assertEqual(state.status, ProjectStatus.IN_PROGRESS)
        self.assertEqual(describe_position(state), "Auditor")

    def test_manual_alignment_can_mark_auditor_revision(self) -> None:
        label = "Auditor revising after Guardian failure"
        state = align_position(WorkflowState(), label)
        self.assertEqual(state.active_agent, Agent.AUDITOR)
        self.assertTrue(state.auditor_revision)
        self.assertEqual(describe_position(state), label)

    def test_manual_guardian_positions_preserve_review_subject(self) -> None:
        for label, subject in (
            ("Guardian reviewing Operator", Agent.OPERATOR),
            ("Guardian reviewing Auditor", Agent.AUDITOR),
        ):
            with self.subTest(label=label):
                state = align_position(WorkflowState(), label)
                self.assertEqual(state.active_agent, Agent.GUARDIAN)
                self.assertEqual(state.guardian_subject, subject)
                self.assertEqual(describe_position(state), label)
        self.assertIn("Project complete", WORKFLOW_POSITIONS)

    def test_skirmish_pass_returns_to_operator(self) -> None:
        state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
        transition = advance(state, "Pass sealed")
        self.assertEqual(transition.next_state.active_agent, Agent.OPERATOR)
        self.assertEqual(
            transition.next_state.workflow_mode,
            WorkflowMode.OPERATOR_SKIRMISH,
        )
        self.assertIsNone(transition.next_state.guardian_subject)
        self.assertFalse(transition.next_state.auditor_revision)
        self.assertIn("next Operator pass", transition.handoff)

    def test_skirmish_not_sealed_stays_open(self) -> None:
        state = WorkflowState(workflow_mode=WorkflowMode.OPERATOR_SKIRMISH)
        transition = advance(state, "Not sealed")
        self.assertEqual(transition.next_state.active_agent, Agent.OPERATOR)
        self.assertIn("current Operator pass", transition.handoff)

    def test_switching_to_skirmish_collapses_role_state(self) -> None:
        triad = WorkflowState(
            active_agent=Agent.GUARDIAN,
            guardian_subject=Agent.AUDITOR,
            auditor_revision=True,
        )
        skirmish = align_mode(triad, WorkflowMode.OPERATOR_SKIRMISH)
        self.assertEqual(skirmish.active_agent, Agent.OPERATOR)
        self.assertIsNone(skirmish.guardian_subject)
        self.assertFalse(skirmish.auditor_revision)
        self.assertEqual(describe_position(skirmish), "Operator skirmish")
        self.assertEqual(
            workflow_positions(skirmish),
            ("Operator skirmish", "Project complete"),
        )

    def test_legacy_state_without_mode_defaults_to_triad(self) -> None:
        state = WorkflowState.from_dict({"active_agent": "Auditor"})
        self.assertEqual(state.workflow_mode, WorkflowMode.TRIAD)
        self.assertEqual(state.active_agent, Agent.AUDITOR)


if __name__ == "__main__":
    unittest.main()
