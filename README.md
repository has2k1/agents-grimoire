# agents-grimoire

Two skills for maintaining useful agent instructions alongside a repository's
code. Bootstrap creates or extends verified instructions. Audit checks whether
existing instructions remain accurate, cover the necessary rules, and still help
future work.

## The system

Update affected instructions in the same commit when a change invalidates a
documented claim or introduces a necessary instruction. Leave accurate
instructions unchanged. Independent documentation corrections,
bootstrap work, and audit records are valid changes too.

Preserve established project policy. When implementation conflicts with a
rule, establish whether the task authorises changing that rule before revising
it. Record architectural decisions when they constrain future work and their
reason is supported by a recorded explanation or the decision-maker's
confirmation. Bootstrap preserves existing explanations without
reconstructing intent from Git history.

Place guidance at the nearest useful scope. Use a root file for project-wide
instructions, optional source-root or package files (hubs) for shared rules,
and local module files (leaves) for distinct module guidance. Keep one
authoritative explanation and use links or short scoped reminders where needed.
Create files only when their content justifies them.

Retain warnings while they prevent a concrete failure or plausible regression.
Remove obsolete or shallow warnings after refactoring; recast a useful warning
as a guardrail when bypassing an abstraction could reintroduce the problem.
Keep applicable versions, verification dates, platforms, and measurement
conditions alongside the claims they limit.

## The skills

| Skill | Use | Result |
| --- | --- | --- |
| [agents-md-bootstrap](skills/agents-md-bootstrap/SKILL.md) | Set up instructions, add guidance, or repeat bootstrap after changes | Merge verified content while preserving policy, explanations, and routing; identify uncertain claims for review. |
| [agents-md-audit](skills/agents-md-audit/SKILL.md) | Check instructions after changes or periodically | Report evidenced defects, unverified checks, and proposed corrections; prepare a self-contained checkpoint message. |

## Installation

Use a Node.js version supported by the [skills CLI](https://github.com/vercel-labs/skills).
From a checkout of this repository, install both skills for your user account:

```sh
npx skills add . --global
```

Select the intended agents in the installer. To install into a particular
project instead, run this from that project and provide the checkout path:

```sh
npx skills add /path/to/agents-grimoire
```

Inspect the available skills without installing them:

```sh
npx skills add /path/to/agents-grimoire --list
```

After updating a local checkout, rerun the installation command to refresh its
installed copies. For supported remote sources, use the CLI's `check` and
`update` commands. Installation does not establish a live link to the author's
working checkout. See the [CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)
for source formats, agent selection, and update options.

## Usage

Start or extend the instruction system:

> Use agents-md-bootstrap to set up agent instructions in this repository.
> Preserve existing rules and create only useful scopes.

Audit it after a refactor, dependency change, or a period of development:

> Use agents-md-audit to check these instructions against the current code.

The audit reads and reports by default. Request corrections or checkpoint
creation explicitly when you want those writes; existing authorisation still
applies.

Verify which instruction files your agent actually reads. Discovery depends
on the harness, launch directory, overrides, configuration, and context limits.
Use explicit file reads when automatic loading is unverified. Instruction
files communicate the maintenance expectation; following it still requires
verification and judgement.

## Audit checkpoints

A checkpoint stores the authoritative audit report in an empty, single-parent
Git commit titled:

```text
chore: record agent documentation audit
```

Its parent is the audited revision: the committed snapshot the report examined.
The message contains `##` sections for coverage, unverified checks, new
findings, carried findings, and closed findings, followed by structured
trailers. It remains interpretable from repository history alone.

Only a completed audit becomes a checkpoint. A completed audit has finished its
declared checks of the whole repository and stated its verification limits. It
can still report known defects or unavailable checks. A clean result means no
defect was demonstrated within the checks performed. An unfinished or
interrupted audit produces a report but no checkpoint, so it leaves the baseline
unchanged.

Use the nearest checkpoint on the branch as the baseline for a later audit. It
sets the history boundary, the revision after which the audit inspects changes,
and its new and carried findings are the complete set of open findings. The
audit skill defines the conditions a commit must meet to be a checkpoint.
Rewriting history can break them, so check them again afterwards; create durable
checkpoints after integration when feature branches are squashed.

Preserve each finding's ID and the checkpoint that first recorded it, and repeat
unresolved findings with their evidence. Record each closure once and omit it
from later reports.

Request checkpoint creation after auditing a committed snapshot:

> Record this audit as an empty Git checkpoint with the complete report in
> its message.

Use the [audit skill](skills/agents-md-audit/SKILL.md) for the message format,
selection rules, and write verification. Checkpoints do not require an
external tracker, a separate checkpoint file, or a mutable latest pointer.

## Development

Keep both skills and the repository rules in agreement when changing their
behaviour. Validate realistic outcomes using the [evaluation protocol](evals/README.md).
Format checks cannot establish that a prompt preserves policy or detects
actual drift.

## Licence

MIT. See [LICENSE](LICENSE).
