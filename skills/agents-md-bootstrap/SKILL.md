---
name: agents-md-bootstrap
description: "Create or extend repository agent instructions from current, verifiable project knowledge. Use for initial AGENTS.md setup, adding module guidance, or repeating bootstrap after changes. Preserve existing policy, explanations, and instruction routing without unnecessary rewrites. Use agents-md-audit to check an existing system for drift."
---

# AGENTS.md Bootstrap

Create useful instructions for future changes. Document current commands,
behaviour, and non-obvious constraints supported by the repository. Preserve
established project policy and recorded rationale. Keep uncertain claims out
of the generated instructions and identify them in the handoff.

Treat the instruction system as the repository's applicable instruction files
and the links, imports, and overrides that determine when they are read.
Extend an existing AGENTS.md or CLAUDE.md arrangement without replacing its
routing merely to adopt a new layout.

## Instruction survey

Before writing, inspect the repository state and instruction routing:

- Read existing `AGENTS.md`, `CLAUDE.md`, relevant overrides, imports, and links
  within the requested scope, plus ancestor instructions that apply to it.
- Identify which sources own each rule, where they apply, and any conflicts.
  Check ignored and untracked files as well as Git's tracked inventory.
- Select the path that matches the request: create useful instructions for
  initial setup, retain unrelated sections and add the requested coverage for
  an extension, or correct only inaccurate claims and necessary omissions for
  a repeat run. Leave an unchanged system substantively unchanged.
- Map the natural module boundaries and read enough code to establish each
  proposed instruction. A directory alone does not justify a leaf file.

Preserve release, testing, architectural, and workflow requirements even when
they are not enforced by code. Treat a disagreement between code and policy
as a conflict to resolve under the task's authority. Keep unaffected work
moving and report any conflict that requires a decision.

## Evidence

Distinguish what the implementation proves from what the project requires:

| Content | Evidence | Treatment |
| --- | --- | --- |
| Commands and behaviour | Current configuration, source, tests, or a reproduced invocation | Record the command's purpose, prerequisites, and verified limits. |
| Project policy | Existing applicable instructions or an authorised decision | Preserve the requirement; do not infer a replacement from code. |
| Architectural rationale | An explanation already recorded in current source or documentation | Preserve its supported meaning and applicability. |
| Measurements and workarounds | Evidence with relevant versions, verification dates, platforms, and measurement conditions | Retain those limits while the claim applies. |

Find commands in the actual project configuration or documentation. Run
appropriate, bounded checks when feasible. Record an unavailable prerequisite
or a failing implementation separately from a defective invocation; neither
automatically makes the command stale. Include only the verification that a
command actually provides.

Verify each new or revised factual rule before handoff. Check the relevant
entrypoints, input forms, branches, and existing tests for counterexamples.
State which APIs or modes the rule applies to. Behaviour in one helper does
not establish an invariant for every caller. Complete these checks for the
selected scope before treating the run as finished.

Use current sources for bootstrap rationale. Do not mine Git history for
reasons, reconstruct rejected alternatives, or turn an import pattern into an
invented architectural intention. Preserve existing explanations supported by
their recorded source; leave new rationale to an evidenced decision during
later work. Prefer a short instruction that affects a future change over a
catalogue of symbols or facts obvious from a filename.

## Placement and delivery

Use the following scopes where they carry distinct instructions:

| Scope | Usual location | Purpose |
| --- | --- | --- |
| Repository | Root `AGENTS.md` | Project orientation, useful commands, established policy, maintenance contract, and routing. |
| Shared architecture | A source-root or package file (a hub) | Rules shared by several modules and a map to relevant instructions. |
| Module | A file in the nearest relevant module directory (a leaf) | Its commands and behaviour, non-obvious conventions, and links to shared rules. |

Use one file for a small project if that is sufficient. Add hubs only for
genuinely shared rules and leaves only for independent module knowledge.
Support multiple source roots when the repository has them. Keep one canonical
explanation at the nearest shared scope; use short scoped reminders and links
when a reader could otherwise miss a cross-module obligation.

### Harness delivery

Check the intended harness's filename support, precedence, launch directory,
imports, and exposed loading configuration. Distinguish confirmed automatic
discovery from files deliberately read during this task. An explicit read
does not prove that a future session will receive the file automatically.
Report delivery as unverified when the runtime does not expose enough evidence.

Measure instruction sizes along relevant loading paths and compare them with
the applicable verified budget. Shorten repeated material or move detailed
explanations behind explicit read conditions when a path is too large. Preserve
existing routing; add repository-local compatibility links or imports only
when their semantics are verified. Leave user-wide settings and budget changes
to an explicit request.

## Writing

Merge useful sections into existing files rather than replacing them with a
standard outline. For a new root, include a brief project description, verified
commands with their purpose and prerequisites, established project rules, the
maintenance contract below, and an index of instructions that actually exist.

For a new hub or leaf, state its responsibility, commands and behaviour, and
non-obvious constraints; link to the relevant shared rules and neighbouring
instructions. Omit empty sections. Preserve applicable version limits, but
remove obsolete progress narration and inapplicable history from material
you revise.

Include this maintenance contract verbatim when creating a root file. For an
existing contract, merge missing obligations while preserving stricter
applicable policy and resolving contradictions; avoid duplicate contracts.

> ## Maintaining these files
>
> Update affected instructions in the same commit when a change invalidates a
> documented fact or introduces a necessary instruction. Leave accurate rules
> unchanged. Independent documentation corrections, bootstrap work, and audit
> repairs are legitimate changes.
>
> Treat established project policy as a constraint on implementation. Resolve
> conflicts using the task's authority and applicable instructions; an
> intentional code change alone does not authorise rewriting the policy.
>
> Keep the canonical explanation at the nearest shared scope. Link to it from
> other files, using short scoped reminders where they help readers discover
> an obligation. Retain relevant versions, verification dates, platforms, and
> measurement conditions; remove these limits when they cease to apply.
>
> Record an accepted architectural decision when future changes need a
> non-obvious constraint or its reason. State the rule, its evidenced reason,
> and conditions for reconsideration. Use a recorded explanation or the
> decision-maker's confirmation; keep substantial alternatives in a linked
> decision record. Revise or remove the instruction when its premises change.
>
> Retain a warning about a failure (a trap entry) only when a concrete failure
> or regression path still warrants guidance on diagnosis or prevention. Record
> the symptom, mechanism, and recognition or avoidance. Remove obsolete or
> shallow detail and lessons adequately covered by enforcement or tests. When bypassing an
> abstraction can reintroduce the failure, keep a concise guardrail and its
> reason. Keep historical incident accounts in Git rather than in these files.

## Handoff

Review the resulting diff against the original instruction inventory. Confirm
that established constraints remain, additions are supported, links resolve,
and unchanged sources have not acquired duplicated contracts or empty tiers.

Report the files created and changed, their scopes, constraints preserved,
possible invariants needing confirmation, commands verified, delivery checks,
and unresolved claims or conflicts. State any prerequisites that prevented
verification. A repeat run against unchanged code and instructions should
produce no substantive diff.

Treat the result as candidate documentation. Hand off to
[agents-md-audit](../agents-md-audit/SKILL.md) to verify it, account for findings
from the latest checkpoint, and establish a valid audit baseline. A checkpoint
stores the report of a completed repository-wide audit in an empty Git commit;
a validated checkpoint can supply the history boundary for a later audit.
Bootstrap alone establishes no verified checkpoint. Preserve the repository's
existing commit and publication workflow.
