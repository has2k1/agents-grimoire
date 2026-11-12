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

## Coverage

Record coverage as the files, claims, history, and checks actually examined.

1. Record the repository revision and working-tree state. Inventory instruction
   files, relevant ancestor rules, overrides, imports, links, and module maps in
   the repository. Include existing CLAUDE.md systems rather than assuming
   that AGENTS.md is their active entrypoint.
2. Confirm which files the intended harness discovers and which require explicit
   reads. Check relevant loading paths and size budgets against the available
   configuration or current harness documentation. Mark unknown delivery as
   unverified; filenames and directory placement alone do not prove loading.
3. State files and claims to verify, any sampling, command prerequisites, and
   the available history. Limit the verdict when the repository is dirty,
   history is shallow or unavailable, or checks cannot run. Audit local changes
   separately from a committed snapshot; do not attribute them to its SHA.

## History and earlier findings

For a Git repository, select the baseline before checking intervening changes.
Without Git history, check the current state and report that historical
verification is unavailable.

A **completed audit** has finished its declared checks of the whole
repository; it can report defects, sampling, and unavailable checks with
explicit limits. A clean result means no defect was demonstrated within the
completed checks. An audit that cannot finish produces a report but no
checkpoint.

A **checkpoint** is an empty, single-parent Git commit whose message stores the
report of a completed audit and the trailers of the **Checkpoint message**
template. Its sole parent is the **audited revision**, the committed snapshot
examined by that audit. Local changes are separate from that snapshot. A commit
is a checkpoint only when it meets every condition under **Baseline
selection**; any other commit is an ordinary commit, whatever its message says.

A **baseline** is the nearest checkpoint on the target branch's first-parent
history. It sets the **history boundary**, the revision after which the audit
inspects changes up to the audited revision. Its New and Carried findings are
the complete set of open earlier findings. An audit that produces no checkpoint
leaves the baseline unchanged.

Bootstrap output remains candidate documentation until verified and cannot by
itself supply a baseline.

### Baseline selection

Walk the target branch's first-parent history from HEAD. Treat commits with an
`Agents-Audit-Version` trailer as candidates; identify them by the trailer
rather than the subject. For example:

```sh
git log --first-parent --format='%H' --grep='^Agents-Audit-Version: 1$' HEAD
git show -s --format=%B <candidate> | git interpret-trailers --parse
```

These commands find candidates. A candidate is a checkpoint only when its
message and Git objects meet all of these conditions:

- Every trailer in the message template has one non-conflicting value, the
  version is supported, and the skill revision or content hash is identifiable.
- The commit has exactly one parent. That parent's full SHA equals
  `Agents-Audit-Commit`, and both the parent and commit trees equal
  `Agents-Audit-Tree`. Tree equality alone cannot detect replay onto a
  different history that happens to produce the same files.
- The commit lies on the target's first-parent history.
- `Agents-Audit-Previous` names the nearest earlier checkpoint on the audited
  revision's first-parent history, or `none` for an explicitly established
  initial history boundary. The named commit must itself be a checkpoint.
- The message contains every report section of the template, with declared
  coverage. Unless `Agents-Audit-Previous` is `none`, each ID under New
  findings or Carried findings in the named checkpoint appears under Carried
  findings or Closed findings.

Because each predecessor must itself be a checkpoint, check candidates from the
oldest forward and reuse each result; every commit is then checked once.
Select the nearest candidate that meets these conditions as the baseline.
When a predecessor is unavailable or shallow history prevents these checks,
state the gap. Do not silently replace a known history boundary with the last
few commits or declare the work a first audit. If no baseline can be
established, check the current state within explicit limits and leave
historical coverage unverified. For a genuine first audit with no earlier
checkpoint, verify the current state and state an explicit initial history
boundary.

Rebase, cherry-pick, and squash give commits new parents, so check the
conditions again after rewriting history. Establish durable checkpoints after
integration when feature history is squashed.

## Checks

### Accuracy and policy

- Verify commands against project configuration and their prerequisites. Run
  feasible checks in a suitable environment. Attribute failures to a stale
  invocation, an implementation defect, an unavailable prerequisite, or an
  incomplete check; a valid test command finding a regression is not stale.
- Resolve named references, paths, imports, and module-map entries. Inspect
  renames, shared ownership, and applicable ancestor rules before calling an
  instruction missing. Demonstrate the defect, then judge its severity by the
  likely consequence for an agent following the instruction, not by a missing
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
history boundary. Map each relevant change to claims it might invalidate,
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
Leave a rejected alternative worth mentioning to a comment in the source it
affects, where an agent changing that code will find it. During bootstrap,
continue to use only current sources; do not mine Git history for reasons or
invent rationale.

For significant diagnosed bugs, check whether the lesson still prevents a
costly or repeated mistake. Propose a concise entry recording the symptom,
mechanism, and recognition or avoidance only when it adds useful guidance.
When bypassing an abstraction could reintroduce the failure, recast the warning
as a concise guardrail and explain why. Propose deletion when the mechanism is
gone, the mistake is shallow, or enforcement already carries the lesson
adequately. Keep uncertain mechanisms as proposals for confirmation.

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

Recheck every open finding from the baseline and place it under Carried
findings or Closed findings before finalising the report.

Separate findings into these sections; write `None` when one is empty:

- Record new findings with fresh stable IDs, affected instructions, evidence,
  consequences, and required corrections.
- Carry every unresolved finding from the baseline, including those it listed
  as new, with its ID, its source checkpoint (the checkpoint that first recorded
  it), and a complete account of its evidence, consequence, and required
  correction. Keep a finding open when its resolution cannot be verified, and
  disclose evidence that cannot be validated.
- Close findings with the verified resolution or supersession and supporting
  evidence. Record each closure once, then omit it from later reports. Keep its
  history in the earlier checkpoint rather than growing an archive in each
  report.

Allocate IDs without reusing retired ones; for example, use an audit-specific
UTC timestamp plus a counter and retain that ID thereafter. State in the report
whether the audit completed; an interrupted or unfinished audit ends with the
report. Claim a clean result only within the checks that demonstrate it.

## Checkpoint message

Prepare the following message as part of a completed audit's deliverable.
Include the audit report itself, not pointers to an external issue tracker, a
local report, or another external source. Use the unheaded subject and trailers
exactly as shown, with `##` headings and blank lines for the report sections.
Record complete object IDs and an identifiable skill revision or hash rather
than relying on an installed path.

```text
chore: record agent documentation audit

## Coverage

Examined <repository-relative instruction files or directories>.
Verified <claims and checks performed, including any sampling>.
Inspected history from <history boundary> to the audited revision.
Used <relevant environment and tool versions>.

## Unverified checks

<Checks not completed and their reasons, or None.>

## New findings

<Stable ID, affected instruction and section, finding, evidence,
consequence, and required correction for each new finding; or None.>

## Carried findings

<Stable ID, source checkpoint, and a self-contained account of each
unresolved finding, including evidence, consequence, and required
correction; or None.>

## Closed findings

<Stable ID, resolution or supersession, and supporting evidence
for each finding this audit closes; or None.>

Agents-Audit-Version: 1
Agents-Audit-Commit: <full audited parent commit SHA>
Agents-Audit-Tree: <audited tree SHA>
Agents-Audit-Skill-Revision: <skill revision or content hash>
Agents-Audit-Previous: <baseline checkpoint SHA or none>
```

## Checkpoint creation

Create a checkpoint only for a completed audit and only with authorisation for
that write. Require the audited revision still to be HEAD and the audited
instructions and code to be represented in its tree. Commit authorised
corrections first and verify that resulting snapshot before recording its
checkpoint. Refresh the report and trailers to describe that verified snapshot
if corrections changed the audited revision. Exclude uncommitted or ignored
content from claims about the committed snapshot and record any resulting
coverage limit. Refuse to record a checkpoint for an observed dirty state as
though the parent contained it.

Write the message to a file outside the checkout so the report reaches Git
byte for byte and the working tree stays as recorded. Record HEAD, the index
tree, and existing working changes for the check afterwards. Create the commit
with `--only` so an unrelated staged change stays staged:

```sh
git commit --allow-empty --only --cleanup=verbatim --file <temporary-message-file>
```

Verify afterwards that the checkpoint has the audited revision as its sole
parent, its tree is unchanged, the stored message retains the report and `##`
headings, and the index and unrelated working changes remain intact. Report an
unexpected hook or write result; do not silently modify the report or create
another checkpoint. Exclude checkpoint commits when counting commits that
change code and instructions together. Use Git history as the checkpoint store
without a tracked checkpoint file or mutable latest pointer.
