# Operator Skirmish Mode

Operator Skirmish is Orchestra's single-agent research workflow. It preserves Orchestra's provenance, p-b-v chronology, archive manifests, falsification discipline, and immutable sealed-pass model while collapsing the Operator / Guardian / Auditor routing topology into one accountable Operator.

## Execution model

A Skirmish pass is one coherent loop:

1. Frame the branch question and terminal condition.
2. Construct the candidate argument, instrument, or artifact.
3. Attack it with falsifiers, negative controls, regressions, and counterexamples.
4. Audit authority, lineage, claims, notation, package structure, and inherited state.
5. Seal the pass or keep it open.

The Operator owns all five steps. There are no `origin_role` / `target_role` handoffs and no synthetic Guardian or Auditor events.

## Project mode

Orchestra stores the governance model in `.project-handoff/state.json` as:

```json
{"workflow_mode": "operator_skirmish"}
```

Legacy projects with no `workflow_mode` remain `triad` automatically.

Use **Workflow → Set workflow mode…** to switch an opened project between:

- **Triad**: Operator → Guardian → Auditor routing.
- **Operator Skirmish**: one Operator owns construct, attack, audit, and seal.

Changing mode is itself recorded in the event journal. Switching to Skirmish collapses any active Guardian/Auditor routing state back to Operator without rewriting historical archive manifests.

## Skirmish results

The result surface is:

- `Pass sealed`
- `Not sealed`
- `Project complete`

`Not sealed` records work in the current version. It does not advance p-b-v.

A sealed pass is the authority that may create the successor coordinate:

- **Continue**: `pX-bY-vN → pX-bY-v(N+1)`
- **New branch**: next branch, version 1
- **New phase**: next phase, branch 1, version 1

The first archived interaction remains a structural bootstrap and must use Continue.

## Archive manifests

Skirmish manifests include:

```json
{
  "workflow_mode": "operator_skirmish",
  "source_agent": "Operator",
  "next_agent": "Operator"
}
```

A non-bootstrap coordinate created by a sealed Skirmish pass records:

```text
coordinate_authority = OPERATOR SKIRMISH PASS
```

Triad archives retain their existing `AUDITOR RESULT` authority semantics.

## Package standard

The canonical research package for this mode is **Orchestra Research Package Template v2.1 — Operator Skirmish Edition**.

The package preserves the substantive Orchestra v2.0 surfaces, including:

- stable `p#-b#-v#` identity;
- immutable parent lineage;
- `parent_package_id` and `parent_manifest_sha256`;
- `AUTHORITY.md` with authority hash, scope, exclusions, and conflict law;
- the full claim ledger with evidence class, burden, falsifier, support, contradiction, and status;
- no-I/O executable claim notebooks where used;
- negative controls and rejected mechanisms;
- deterministic manifests and SHA-256 custody;
- immutable sealed ZIPs.

The role-routing metadata and separate Guardian/Auditor adjudication surfaces are intentionally absent because they have no referent in a single-agent Skirmish.

## Compatibility law

Skirmish is additive. It does not reinterpret or migrate historical Triad archives. Existing projects without a mode field load as Triad, and old archive manifests remain readable as written.
