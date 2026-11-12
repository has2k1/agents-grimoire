# AGENTS.md

Maintain two skills for a living agent-instruction system. The bootstrap
creates or extends verified instructions; the audit checks their accuracy and
records audit reports in empty Git commits called checkpoints. README.md
explains the package for users.

## Layout

- Read `skills/agents-md-bootstrap/SKILL.md` when changing setup, preservation,
  placement, delivery checks, or the generated maintenance contract.
- Read `skills/agents-md-audit/SKILL.md` when changing drift checks, rationale,
  finding lifecycle, baseline selection, or checkpoint creation.
- Read `evals/README.md` when validating prompt behaviour or Git checkpoints.

## Paired rules

Change both skills when the shared model changes. Update this file and the
README in the same change when their guidance is affected. Preserve accurate
instructions; an unrelated code change does not require a documentation edit.
Independent corrections and audit records are legitimate changes.

Use current, verifiable project material at bootstrap. Preserve existing
instructions and recorded explanations. Keep inferred intent and rationale
mined from Git history out of generated bootstrap content. Distinguish
established policy from implementation facts; resolve conflicts using the
task's authority rather than assuming that intentional code makes policy
obsolete.

Place canonical explanations at the nearest shared scope and use concise
linked reminders where they improve discovery. Create a hub or leaf only for
distinct useful guidance. Verify instruction delivery and applicable budgets
in the actual harness; explicit reads do not establish automatic discovery.

Record architectural decisions when future work needs a non-obvious constraint
or reason supported by a recorded explanation or the decision-maker's
confirmation. Retain relevant versions, verification dates, platforms, and
measurement conditions. Remove qualifications and rationale when their
premises cease to apply.

Retain failure warnings (trap entries) only when a concrete failure or
plausible regression still warrants guidance. Remove obsolete or shallow
detail and lessons adequately covered by enforcement or tests. Recast
warnings about bypassing abstractions as concise guardrails when their
reasons still matter. Keep the bootstrap contract consistent with the audit
skill's two trap checks: the existing-warning bullet under "Accuracy and
policy" and the proposed-warning paragraph under "Decisions and warnings".

## Checkpoints

Keep audits read-only by default, including the index and HEAD. Prepare a
complete report and proposed corrections. Apply changes or create a checkpoint
when the request authorises that write phase; recognise existing authorisation.

Store the authoritative checkpoint report in the message of an empty,
single-parent Git commit. Use `##` report headings and the title
`chore: record agent documentation audit`. Preserve stable finding IDs and the
checkpoint that first recorded each finding across New findings, Carried
findings, and Closed findings. Repeat unresolved evidence, record closures once, and use
`None` for empty sections. Keep the record interpretable from Git alone. Record
only completed audits of the whole repository as checkpoints; an interrupted or
unfinished audit produces a report without one.

Use the audit skill as the canonical source for checkpoint trailers,
validation, and write commands. Use the nearest checkpoint as the baseline: it
sets the history boundary, and its New and Carried findings are the open
findings. Treat a commit that fails the checkpoint conditions as an ordinary
commit, and check those conditions again after rewritten history. Exclude
checkpoint commits from counts of commits that change code and instructions
together.

## Skill writing

Keep the names `agents-md-bootstrap` and `agents-md-audit`. Use valid YAML
frontmatter with names matching the directories. Write descriptions that
identify the task and intended trigger accurately; update them when scope
changes.

Require readable prose throughout: define the package's terms before using
them, name actions and conditions directly, and group related rules. Then
make agent triggers, ordering, exceptions, and completion explicit. Preserve
every obligation when simplifying. Write actionable instructions in the
imperative and explain non-obvious requirements. Use British English in
authored prose. Preserve upstream API spellings. Prefer concise
self-contained skills; add a supporting reference only for substantial
conditional detail and link it at its loading condition.

## Verification

Run `git diff --check` for whitespace and `npx skills add . --list` for local
skill discovery. Use the evaluation protocol for behavioural validation;
format checks alone cannot prove accurate claims, preservation, or useful
findings.

Run trials in disposable snapshots and record their exact revisions, relevant
ignored instructions, runner information, outcomes, and verification limits.
Keep supplementary trial evidence and source-history corrections in dated
local artefacts. Record the verification date and applicable version when
promoting measured evidence into durable documentation.

Keep this root file in the candidate tracked tree despite user-wide ignore
rules. Keep local session material, plans, reports, and trial outputs outside
the package. Preserve the repository's commit and publication workflow.
