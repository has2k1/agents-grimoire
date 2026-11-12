# Behavioural evaluation

Evaluate the skills through observable repository changes and evidence-backed
reports. A format check cannot show whether a prompt preserves policy or avoids
false findings. Keep expected outcomes separate from the agent's input and judge
the resulting files, commands, and report against the source snapshot.

## Workspaces

Use disposable copies of three real repositories: a small package, a project
with established instructions, and a larger hierarchy. Pin each copy to a
source revision. Copy applicable ignored or untracked instruction files
explicitly and record their contents and provenance; a Git clone alone can
omit them. Capture the initial file hashes, staged entries, raw index state,
HEAD, status, and relevant refs. Set `GIT_OPTIONAL_LOCKS=0` during read-only
Git inspection and keep reports, test caches, and other outputs outside the
target. Leave the source checkouts untouched.

Create separate disposable histories for controlled defects and checkpoint
mechanics. Label introduced conditions as evaluation fixtures, rather than
presenting them as incidents from the original project. Keep fixture scripts,
run outputs, and dated evidence outside the shipped skill directories.

## Runs

1. Define the request, snapshot, expected outcome, and correctness checks before
   invoking a skill. Give the executing agent the request, skill, and source
   material without the expected answer.
2. Run initial bootstrap, repeat bootstrap, and a read-only audit on each real
   snapshot. Compare the resulting content and recorded repository state.
   Verify read-only preservation separately from the correctness of findings.
3. Run controlled drift cases independently or with clearly separable evidence.
   Classify an unexpected finding by its evidence before calling it a false
   positive. Accept a clean audit when no defect is demonstrated.
4. Verify loading from the repository root and one nested directory in the
   intended harness. Record which files actually reached the agent; separate
   automatic delivery from a deliberate read.
5. Exercise checkpoint creation only in disposable repositories with explicit
   authorisation. Recover the report from a fresh clone without local artefacts
   or an external issue tracker.
6. Run one bounded change task with and without generated instructions on
   equivalent snapshots. Fix the task, correctness checks, and runner settings
   before either run. Report correctness, policy preservation, unnecessary
   documentation edits, and investigation effort without assuming improvement.
7. Record each result as passed, failed, or unverified, with the actual
   evidence. Rerun affected cases after a prompt correction; retain successful
   results when neither their inputs nor the relevant rule changed. Record which
   final skill bytes each result exercises and why broader cases were omitted.

## Cases

| Case | Expected outcome |
| --- | --- |
| Bootstrap a small repository | Create only justified files containing verified claims and no invented rationale. |
| Extend an existing root | Preserve established policy and unrelated sections while adding the requested coverage. |
| Repeat bootstrap on unchanged code | Produce no substantive changes or duplicate maintenance contract. |
| Infer a rule from a shared helper | Check the relevant entrypoints and input forms; state which forms the rule covers when their behaviour differs. |
| Optimise private code while preserving a precise invariant | Leave accurate instructions unchanged and report no maintenance defect solely from absent documentation edits. |
| Remove a command or rename a referenced file or API | Identify the affected claim and support its correction with repository evidence. |
| Run a valid test command that detects a code failure | Attribute the failure to the implementation rather than the invocation. |
| Run a command with an unavailable prerequisite | Report the missing prerequisite and limit the verification claim. |
| Introduce code that conflicts with established policy | Identify the conflict without declaring the policy wrong merely because the change is intentional. |
| Record an architectural decision independently of a bug fix | Propose rationale only from an evidenced decision or author confirmation. |
| Remove a failure mechanism or leave a bypassable guardrail | Propose deletion or a useful guardrail according to the concrete remaining regression path. |
| Retain a workaround for a current version | Preserve its version, date, platform, and measurement conditions while they remain relevant. |
| Limit history or leave instruction loading uncertain | State the coverage or delivery limit without inventing a universal verdict. |
| Establish a first checkpoint | Verify the committed snapshot and state the initial history boundary; treat bootstrap alone as insufficient. |
| Advance through three completed checkpoints | Preserve IDs, distinguish new and carried findings, record closures once, and repeat enough open evidence for each record to stand alone. |
| Interrupt an audit | Produce a report without a checkpoint and leave the baseline unchanged. |
| Encounter malformed checkpoint trailers or unavailable predecessors | Treat a commit that fails the checkpoint conditions as an ordinary commit; disclose the history limit when a predecessor is unavailable. |
| Replay, rebase, or squash checkpoint history | Check the conditions again on rewritten commits; establish a new checkpoint when none still qualifies. |
| Create a checkpoint with unrelated staged changes | Create a single-parent empty checkpoint while preserving index entries and staged contents. |
| Configure comment-stripping message cleanup | Preserve the authored `##` headings and report through explicit verbatim cleanup. |
| Recover a checkpoint from a fresh clone | Read its coverage, limitations, findings, and evidence entirely from Git history. |

## Comprehension review

Read the README and both skills as a technical maintainer unfamiliar with the
design discussion. Check definitions, paragraph transitions, branch conditions,
exceptions, completion criteria, and links. Use an independent reader when
available. Supply the candidate documents and ordinary reading questions,
without expected answers or prior conclusions.

Ask the reader to explain when to use each skill, what bootstrap preserves and
may infer, what makes an audit complete, which record supplies its baseline and
findings, and what permits a write. Require locations supporting each answer
and flag rules that require reconstruction from scattered passages. Resolve
material ambiguities and repeat the affected questions.

Record whether the reader is an agent or a human. Treat an agent's answers as a
proxy for comprehension; claim human testing only for an actual human reader.
Keep editorial judgement separate from prompt behaviour and Git properties.
Use correctness and the ease of following the procedure rather than a numerical
readability score or word-count target.

## Checkpoint evidence

Inspect the commit object and repository state directly. Confirm that the
checkpoint has one parent, its tree equals the audited snapshot's tree, its
stored message preserves the authored report, and unrelated staged content is
unchanged. Discover candidates through first-parent history and inspect their
structured metadata rather than relying on the subject line.

Use a three-checkpoint sequence with independently specified findings: open two
findings, carry one and close the other while adding a third, then carry the
third and close the second. Check that the final report contains the remaining
open evidence and only the latest closures. Read earlier commits to confirm that
older findings remain recoverable without being copied indefinitely.

Include a replay whose tree is unchanged but whose parent or inspected history
differs. Tree equality establishes file equality, not the validity of an earlier
history-based conclusion. Test predecessor ancestry and target identity with
separate candidates that each fail one condition. Verify the baseline decision
as well as the Git mechanics; a successful empty commit does not by itself
validate the audit skill's selection procedure.

## Run record

Store a dated record with exact target revisions, skill content hashes,
copied local instructions, runner and model versions where exposed, prompts,
outputs, diffs, commands, and limitations. Link each case to observed
evidence and state whether it exercised a model decision, a Git property, or
a static format check. Keep unrun cases outstanding. Preserve the
authoritative audit report inside any checkpoint message; supplementary
trial logs do not replace it.
