---
name: agents-md-audit
description: "Check existing AGENTS.md or CLAUDE.md instructions against project evidence and policy. Use for periodic reviews, drift checks after changes, or establishing or continuing a Git audit record. Report defects and verification limits, retain unresolved findings, and prepare a checkpoint message. Apply corrections or create the checkpoint only when authorised."
---

# AGENTS.md Audit

Audit instructions against the project state and established policy. Prioritise
claims that could mislead an agent. Document shape and edit frequency alone do
not establish a defect. Report no defect when the checks demonstrate none;
brief bootstrap documentation and unchanged accurate instructions can be enough.

Keep the audit read-only by default, including the index and Git history.
Prepare corrections and a checkpoint message for review. Apply fixes or create
a checkpoint when the request authorises that action; use existing authority
without asking for it again. Run checks without auto-fix or other source-writing
options, and report execution prerequisites that are unavailable.

## Scope

Define the audit's scope as the repository or directory being checked, together
with the claims and limits of the review. Record coverage as the files, claims,
history, and checks actually examined. A directory name alone does not establish
complete coverage.

1. Record the repository revision and working-tree state. Inventory instruction
   files, relevant ancestor rules, overrides, imports, links, and module maps in
   the requested scope. Include existing CLAUDE.md systems rather than assuming
   that AGENTS.md is their active entrypoint.
2. Confirm which files the intended harness discovers and which require explicit
   reads. Check relevant loading paths and size budgets against the available
   configuration or current harness documentation. Mark unknown delivery as
   unverified; filenames and directory placement alone do not prove loading.
3. State files and claims to verify, any sampling, command prerequisites, and the
   available history. Limit the verdict when the repository is dirty, history is
   shallow or unavailable, or checks cannot run. Audit local changes separately
   from a committed snapshot; do not attribute them to its SHA.

## History and earlier findings

For a Git repository, choose the history boundary and collect earlier findings
before checking intervening changes. Keep these decisions separate: a report
can contain findings that must be retained even when it cannot supply the
history baseline. Without Git history, check the current state and report that
historical verification is unavailable.

A **checkpoint** is an empty, single-parent Git commit whose message stores an
audit report and structured trailers. Its sole parent is the **audited
revision**, the committed snapshot examined by that audit. Local changes are
separate from that snapshot.

A **baseline** is an earlier validated, completed checkpoint used to choose the
history window for its scope and demonstrated coverage. A completed audit has
finished its declared work; it can report defects, sampling, and unavailable
checks with explicit limits. A clean result means no defect was demonstrated
within the completed checks. An interrupted or unfinished audit is partial.
Use the **Report** and **Checkpoint message** sections to finish the deliverable.
Bootstrap output remains candidate documentation until verified and cannot by
itself supply a baseline.

### Baseline selection

Discover candidate checkpoints from the target branch's first-parent history,
using the `Agents-Audit-Version` trailer rather than the subject. For example:

```sh
git log --first-parent --format='%H' --grep='^Agents-Audit-Version: 1$' HEAD
git show -s --format=%B <candidate> | git interpret-trailers --parse
```

These commands find candidates; they do not validate them. Check each message
and its Git objects before selecting the nearest applicable completed record:

- Require one non-conflicting value for every trailer in the message template,
  a supported version and status, a normalised repository-relative directory
  scope (`.` for the repository), and an identifiable skill revision or content
  hash.
- Require exactly one parent. Require that parent's full SHA to equal
  `Agents-Audit-Commit`, and require both the parent and checkpoint trees to
  equal `Agents-Audit-Tree`. Tree equality alone cannot detect replay onto a
  different history that happens to produce the same files.
- Require the checkpoint to lie on the target's first-parent history. Use a
  completed checkpoint of the same scope, and limit its use to demonstrated
  coverage. After a partial or narrower audit, retain earlier completed
  baselines for work it did not cover.
- Require `Agents-Audit-Previous` to name the previous applicable completed
  checkpoint on the audited parent's first-parent history, or `none` for an
  explicitly established initial boundary. Validate predecessor records too.
  This trailer identifies the earlier baseline; it does not identify every
  report whose findings must be read.
- Require a self-contained report with declared coverage and all previously
  reported findings in scope accounted for. Reject malformed, conflicting,
  partial, out-of-scope, replayed, or otherwise invalidated records as baselines.

Walk past an invalid candidate to an earlier valid one and report the rejection.
When a predecessor is unavailable or shallow history prevents validation, state
the gap. Do not silently replace a known boundary with the last few commits or
declare the work a first audit. If no reliable baseline can be recovered, check
the current state within explicit limits and leave historical coverage
unverified. For a genuine first audit with no earlier baseline, verify the
current state and state an explicit initial history boundary.

Revalidate surviving records after rebase, cherry-pick, or squash. Establish
durable checkpoints after integration when feature history is squashed.

### Earlier findings

Collect earlier findings independently of baseline eligibility. Read the
baseline's report and subsequent checkpoint reports whose findings overlap the
requested scope, including partial, narrower, and relevant wider-scope reports.
Without a same-scope baseline, inspect relevant records within the declared
history boundary. A missing or invalid baseline limits historical claims; it
does not erase known finding evidence.

Process reports in history order. Preserve finding IDs, identify their source
checkpoints, and honour verified resolutions. Keep uncertain evidence for
verification during the checks and report what cannot be validated under
unverified checks. Exclusion from baseline selection does not close a finding.
Identify known findings outside a narrower audit's scope explicitly; leave them
unresolved and retain the wider scope's baseline.

For example, use completed root checkpoint A as the next root audit's baseline.
If later checkpoint B is partial or covers only `src`, read B for findings too.
Carry B's unresolved findings into root report C with their existing IDs and
source checkpoint. Honour B's verified closures without repeating them in C.
Set C's `Agents-Audit-Previous` to A.

## Checks

### Accuracy and policy

- Verify commands against project configuration and their prerequisites. Run
  feasible checks in a suitable environment. Attribute failures to a stale
  invocation, an implementation defect, an unavailable prerequisite, or an
  incomplete check; a valid test command finding a regression is not stale.
- Resolve named references, paths, imports, and module-map entries. Inspect
  renames, shared ownership, and applicable ancestor rules before calling an
  instruction missing. Judge severity by the likely consequence, not a missing
  symbol alone.
- Verify important invariants against the implementation and tests. Distinguish
  descriptions from policy: intentional code can still violate an established
  boundary. Resolve conflicts using the task's authority and recorded decisions;
  do not rewrite policy merely to match code that violates it.
- Inspect warnings against concrete failure or regression paths. Remove obsolete
  or shallow detail, retain a useful guardrail when bypassing it remains a
  realistic risk, and trim explanations already adequately carried by tests or
  enforcement. Prefer present guidance over a history of fixed failures.

Report demonstrated defects as stale, contradicted, missing, policy conflicts,
or obsolete warnings. Keep uncertain claims under unverified checks. Include the
affected instruction, repository evidence, consequence, and proposed correction.

### Maintenance

Inspect code, configuration, dependency, and instruction changes since the
selected boundary. Map each relevant change to claims it might invalidate,
including unchanged instruction files. Use commit-message keywords and optional
counts of commits that changed code and instructions together to choose changes
for inspection, not to judge documentation quality.

Report a maintenance defect only when a change invalidated a documented claim or
omitted a necessary instruction. Allow a precise invariant to survive many
changes untouched. Treat independent corrections, bootstrap commits, audit
repairs, and checkpoint commits as legitimate work. A cross-module refactor need
not edit instructions whose claims remain true.

### Decisions and warnings

Inspect architectural decisions independently of bug-fix discovery. Look for
accepted choices whose consequence should constrain future changes and whose
reason is not apparent from code. Use a recorded explanation or confirmation by
the decision-maker; a diff proves a change, not its intent. Draft the rule,
reason, and conditions for reconsideration only when evidenced and still useful.
Keep longer trade-offs in an existing decision record and link to it from
concise local guidance. During bootstrap, continue to use only current sources;
do not mine Git history for reasons or invent rationale.

For significant diagnosed bugs, check whether the lesson still prevents a
costly or repeated mistake. Propose a concise symptom, mechanism, and recognition
entry only when it adds useful guidance. When bypassing an abstraction could
reintroduce the failure, recast the warning as a concise guardrail and explain
why. Propose deletion when the mechanism is gone, the mistake is shallow, or
enforcement already carries the lesson adequately. Keep uncertain mechanisms
as proposals for confirmation.

### Form

Check form after accuracy. Place repository-wide rules in the root file,
rules shared by modules in a source-root or package file (a hub), and
distinct module rules in a local file (a leaf). Use only the scopes that
need separate guidance; permit one-file projects, multiple hubs, and omitted
empty sections. Keep one canonical explanation and allow a brief scoped
reminder with a link when it improves discovery. Preserve applicable
versions, verification dates, platforms, and measurement conditions. Remove
obsolete progress narration, invented rationale, unnecessary duplication,
and instructions that no longer help with a change. Judge specificity by
useful decisions, not by how often text changes.

## Report

State whether the checked instructions are accurate and limit that conclusion
to the claims examined. Record the revision, dirty or ignored content examined,
instruction inventory, claims verified or sampled, history boundary, command
outcomes, relevant environment and versions, and unresolved checks. Keep the
report interpretable from the repository itself, using repository-relative
paths and Git revisions as evidence.

Verify the status of each earlier finding against the checks. Preserve its ID
and source checkpoint; retain unresolved findings and disclose evidence that
cannot be validated. Honour supported resolutions in history order. Keep known
out-of-scope findings under Carried findings, explicitly labelled as outside
this audit's scope and not rechecked. Account for every earlier finding in
scope before finalising the report.

Separate findings into these sections; write `None` when one is empty:

- Record new findings with fresh stable IDs, affected instructions, evidence,
  consequences, and required corrections.
- Carry every unresolved finding collected from earlier reports with its ID
  and a complete account of its evidence, consequence, and required correction.
  Move unresolved new findings here at the next checkpoint; retain findings
  whose resolution cannot be verified.
- Close findings with the verified resolution or supersession and supporting
  evidence. Record each closure once, then omit it from later reports. Keep its
  history in the earlier checkpoint rather than growing an archive in each report.

Allocate IDs without reusing retired ones; for example, use an audit-specific
UTC timestamp plus a counter and retain that ID thereafter. Mark the audit
complete when its declared work is finished, even if findings remain or checks
are unavailable with explicit limits. Mark unfinished or interrupted work
partial. Claim a clean result only within the checks that demonstrate it.

## Checkpoint message

Prepare the following message as part of the audit deliverable. Include the
audit report itself, not pointers to Kata, a local report, or another external
source. Use the unheaded subject and trailers exactly as shown, with `##`
headings and blank lines for the report sections. Record complete object IDs and
an identifiable skill revision or hash rather than relying on an installed path.

```text
chore: record agent documentation audit

## Coverage

Examined <repository-relative instruction files or scopes>.
Verified <claims and checks performed, including any sampling>.
Inspected history from <revision> to the audited revision.
Used <relevant environment and tool versions>.

## Unverified checks

<Checks not completed and their reasons, or None.>

## New findings

<Stable ID, affected instruction and section, finding, evidence,
consequence, and required correction for each new finding; or None.>

## Carried findings

<Stable ID and a self-contained account of each unresolved finding,
including evidence, consequence, and required correction; or None.>

## Closed findings

<Stable ID, resolution or supersession, and supporting evidence
for each finding closed since the previous checkpoint; or None.>

Agents-Audit-Version: 1
Agents-Audit-Status: <complete or partial>
Agents-Audit-Scope: <. or repository-relative directory>
Agents-Audit-Commit: <full audited parent commit SHA>
Agents-Audit-Tree: <audited tree SHA>
Agents-Audit-Skill-Revision: <skill revision or content hash>
Agents-Audit-Previous: <previous applicable checkpoint SHA or none>
```

## Checkpoint creation

Create a checkpoint only with authorisation for that write. Require the audited
revision still to be HEAD and the audited instructions and code to be represented
in its tree. Commit authorised corrections first and verify that resulting
snapshot before marking it. Refresh the report and trailers to describe that
verified snapshot if corrections changed the audited revision. Exclude
uncommitted or ignored content from claims about the committed snapshot and
record any resulting coverage limit. Refuse to mark an observed dirty state as
though the parent contained it.

Save the message in a temporary file outside the checkout. Record HEAD, the index
tree, and existing working changes before the write. Keep an unrelated staged
change staged by using the explicit empty-commit mode:

```sh
git commit --allow-empty --only --cleanup=verbatim --file <temporary-message-file>
```

Verify afterwards that the checkpoint has the audited revision as its sole
parent, its tree is unchanged, the stored message retains the report and `##`
headings, and the index and unrelated working changes remain intact. Report an
unexpected hook or write result; do not silently modify the report or create
another marker. Exclude checkpoint commits when counting commits that change
code and instructions together. Use Git history as the checkpoint store without
a tracked checkpoint file or mutable latest pointer.
