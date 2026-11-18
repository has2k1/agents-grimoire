# agents-grimoire

Agent instructions can save you from explaining a repository's conventions in
every coding session. As the code changes, those instructions can become
incomplete or misleading. agents-grimoire provides two skills to help your
coding agent write useful instructions and check that they still match your
project.

The skills work with repository instruction files such as `AGENTS.md` and
`CLAUDE.md`. You can use them to set up instructions for the first time, extend
existing guidance, or review it after a refactor.

## The skills

[**agents-md-bootstrap**](skills/agents-md-bootstrap/SKILL.md) creates or extends
instructions using information the agent can verify in your project. It
preserves existing rules and recorded explanations, adds guidance where it is
useful, and flags uncertain claims for your review. Running it again should
leave accurate, sufficient instructions unchanged.

[**agents-md-audit**](skills/agents-md-audit/SKILL.md) checks existing instructions
against the code and project policy. Its report explains the problems it found,
the proposed corrections, and anything it could not verify. An audit reads and
reports by default; it changes files or records a Git checkpoint when you
authorise those actions.

## Installation

Use a Node.js version supported by the [skills CLI](https://github.com/vercel-labs/skills).
Run this from the project where you want to use the skills:

```sh
npx skills add has2k1/agents-grimoire
```

Select the skills and intended agents in the installer. To install for your
user account instead, add `--global`:

```sh
npx skills add has2k1/agents-grimoire --global
```

Inspect the available skills without installing them:

```sh
npx skills add has2k1/agents-grimoire --list
```

To install from a local checkout, use its path in place of
`has2k1/agents-grimoire`.

After updating a local checkout, rerun the installation command to refresh its
installed copies. For supported remote sources, use the CLI's `check` and
`update` commands. Installation does not establish a live link to the author's
working checkout. See the [CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)
for source formats, agent selection, and update options.

## Usage

After installation, ask your agent to use the skill by name. For an initial
setup, you could write:

> Use agents-md-bootstrap to set up agent instructions in this repository.

The same skill can extend instructions for a particular area:

> Use agents-md-bootstrap to add guidance for the parser package, preserving
> the existing project rules.

After a refactor, dependency change, or a period of development, you could ask:

> Use agents-md-audit to check these instructions against the current code.

The report gives you proposed corrections to review. To have the agent apply
corrections as part of the audit, include that in your request:

> Use agents-md-audit to check these instructions and fix the problems you can
> verify.

Your agent's instruction-loading rules still matter. Different tools and launch
directories can load different files, and context limits may prevent some
instructions from reaching the agent. The skills check this where possible and
report what remains unverified. Creating an instruction file alone does not
guarantee that every session will read it.

## Instruction maintenance

The skills aim to keep instructions useful without turning them into a
catalogue of the code. Project-wide guidance belongs in a root file; shared or
module-specific guidance can live closer to the code it covers. Small projects
may need only one file. Links and short reminders help readers find shared
rules without repeating the full explanation.

The generated guidance asks agents to update affected instructions alongside a
code change when that change makes them inaccurate or creates a need for new
guidance. Accurate instructions can stay unchanged. Documentation corrections
and audits can also happen independently of code changes.

Existing project policy remains a constraint. If the code disagrees with a
rule, the skills treat that as a conflict to resolve rather than assuming the
rule should change. Bootstrap preserves recorded reasons for decisions; it
does not reconstruct intent from Git history.

Explanations and warnings earn their place by helping with future work. The
skills retain relevant constraints, supported reasons for architectural
decisions, and warnings about failures that could recur. They remove obsolete
detail and keep version, date, platform, and measurement limits where those
qualify a claim.

## Audit history

An audit can record its report in an empty Git commit called a **checkpoint**.
The report lives in the commit message, so it remains available in repository
history without a separate report file or external tracker. The commit changes
no files and has the title `chore: record agent documentation audit`.

To request one, ask your agent to audit a committed snapshot and record the
result:

> Use agents-md-audit to audit this repository and record the complete report
> as an empty Git checkpoint.

Later audits use the nearest valid checkpoint on the branch to identify the
changes to inspect and the findings still open. Unresolved findings retain
their IDs and evidence; resolved findings are recorded as closed once.

A checkpoint records a completed audit of the whole repository, including its
verification limits. It can contain defects or checks that were unavailable.
A clean report means no defect was demonstrated within the checks performed.
An interrupted audit produces a report without advancing the checkpoint.

Rewriting Git history can invalidate checkpoints. If your workflow squashes
feature branches, durable checkpoints belong after integration. The
[audit skill](skills/agents-md-audit/SKILL.md) contains the full report format,
baseline rules, and checkpoint validation procedure.

## Development

The two skills share a model of instruction maintenance. Changes to that model
need corresponding updates to both skills and the repository guidance.

Run `make check` before committing. It checks whitespace, skill discovery,
harness lint and types, and a fixture build with its self-test. Behavioural
trials check whether the skills preserve policy and find real problems; their
[evaluation protocol](evals/README.md) explains the process and its limits.

Run `make dev` once in a checkout to make the maintainer skill `run-trials`
available in Codex and Claude Code. Then invoke it by name to run the trials.
The command creates Git-ignored links in `.agents/skills/` and
`.claude/skills/`; the installer does not ship this maintainer skill.

## Licence

MIT. See [LICENSE](LICENSE).
