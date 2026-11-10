---
name: agents-md-audit
description: "Audit an existing AGENTS.md documentation system to evaluate whether it has been maintained well — checking drift between docs and code, the discipline of updating docs in the same commit as code changes, style conformity, and whether recent bug fixes earned 'trap' entries. Reports findings and offers to draft fixes. Use whenever the user wants to check, review, audit, or evaluate the health, freshness, or accuracy of their AGENTS.md / CLAUDE.md files, asks 'are the agent docs up to date', 'have the AGENTS.md files been maintained', or wants to catch documentation drift before it misleads an agent."
---

# AGENTS.md Audit

Evaluate whether a repository's AGENTS.md system is still telling the truth. These files derive their entire value from being trusted by the agents that read them — the moment a command fails, a named type no longer exists, or a documented invariant has been abandoned, the file stops being an asset and becomes a liability, because an agent will confidently follow it into a broken state. The audit's job is to catch that decay before it misleads.

Run this periodically (monthly is a reasonable cadence, or before a release) and after large refactors. It is read-only by default: it reports, and offers to draft fixes, but does not edit files without being asked.

## What "well-maintained" means

A healthy AGENTS.md system has four properties, in descending order of importance:

1. **Accurate** — nothing in the files is false right now.
2. **Disciplined** — docs change in the same commits as the code they describe.
3. **Current** — recent decisions and bug fixes have been captured as rationale and trap entries.
4. **Well-formed** — files follow the tier/skeleton conventions and the project's style rules.

Most audits over-index on #4 (easy to check) and under-index on #1 (the one that actually matters). Weight your effort accordingly.

## The four checks

### Check 1: Drift (does the doc still match the code?)

This is the core of the audit. For each AGENTS.md file, verify its falsifiable claims:

- **Commands.** Every command in the root file should still be real. Check each against `package.json` / `Cargo.toml` / `Makefile` / CI config. Run the fast ones (`--version`, a lint, a check) if feasible. A command that errors is a critical finding.
- **Named references.** Every type, function, module, and file path named in a doc should still exist. Grep for them. A reference to a renamed or deleted symbol is a critical finding — it means the doc survived a refactor that didn't update it.
- **Invariants.** Spot-check the documented load-bearing rules. If a file says "every X must register a Y," confirm the registration mechanism still exists and is still enforced.
- **Module map.** Every module listed should exist; every existing module of consequence should be listed. A module added in code but absent from the map is a discipline finding (Check 2) as much as a drift one.
- **Trap reachability.** For each existing trap / quirk / pitfall entry, ask whether the failure mode it describes can still occur. A refactor sometimes removes the very condition a trap warned about — and the entry, written when the trap was real, outlives it. An entry guarding an unreachable bug is worse than no entry: it plants a false belief about how the code behaves and makes an agent reason around a hazard that can't happen. Judge reachability by what the code permits, not by what the entry hopes:
  - **Unreachable** (the condition is gone) → flag for **deletion**. Delete, don't annotate with "fixed in the refactor" — that's backwards-facing language, and the file describes the present. The history is preserved in git.
  - **Guarded but reachable** (a new abstraction prevents the bug, but an agent could bypass the abstraction and reintroduce it) → **keep, recast**: the entry stops describing a bug and becomes a guardrail rule ("use `Buffer::chunks()`, don't walk by hand — the hand-walk is what double-counts"). Only valid if the abstraction genuinely can't be trivially bypassed; if the internals are easy to reach past, keep the fuller entry naming both the guardrail and why reaching past it is dangerous.

Report drift as **stale** (documented thing no longer exists), **missing** (code reality not documented), **contradicted** (doc says X, code does Y), or **unreachable** (a trap entry whose failure mode a refactor eliminated).

### Check 2: Discipline (do docs change with the code?)

This is the check most audits skip, and it's the one that predicts future health. Use git.

For a window of recent history (default: since the last audit, or the last ~50 commits):

- **Find code commits that touched a module but not its AGENTS.md.** `git log` the module path, and for each commit check whether the corresponding doc file changed in the same commit. A commit that meaningfully changed a module's behavior without touching its doc is a discipline gap — the doc may now be stale (feed those commits into Check 1 for verification).
- **Find doc-only commits.** A commit that changes an AGENTS.md file with no accompanying code change is a smell: it usually means the doc fell out of an earlier change and someone patched it up later. Occasional ones are fine (rewording, fixing typos); a pattern of them means the same-commit discipline isn't holding.
- **Cross-module changes.** A refactor touching many modules should have touched many doc files in the same commit.

Quantify loosely: "of the last N commits touching `src/auth/`, K also touched `src/auth/AGENTS.md`." A high K with low drift is a healthy system. A low K *with* low drift means the docs were vague enough to survive changes (a different problem — they're not specific enough to go stale, which often means not specific enough to be useful).

### Check 3: Missing rationale and trap entries (has recent history been captured?)

The files grow by incident. Check whether they actually did:

- **Recent bug-fix commits without trap entries.** Identify commits that look like non-trivial bug fixes (message mentions "fix", "bug", "regression", "panic", "crash", or references an issue) whose module file has no corresponding trap/quirk/pitfall entry. For each significant one, the fix is a candidate for documentation.
- **…but only reachable ones.** Before drafting, check whether the fix — or a later refactor — removed the condition that made the bug possible. A bug that can't recur earns no entry. If a refactor merely made it shallow behind an abstraction that could be bypassed, draft the guardrail form instead ("use X, don't do Y — Y is what caused this"), not the bug narrative.
- **Draft the surviving trap entries.** This is the audit's most valuable output. For each reachable candidate, read the fix commit and its diff, then *offer* to draft a short entry recording: the **symptom** (what a user/observer saw), the **mechanism** (why it happened), and the **recognition** (how to spot it or avoid it next time). Present these as proposals — the human who made the fix confirms the mechanism; you draft the words. Do not add them unasked.
- **Retire the dead ones.** Symmetric with drafting: existing trap entries that Check 1 found unreachable should be proposed for deletion here, so the trap library reflects only hazards that can still bite. A trap file that grows monotonically is a smell, not a strength.

### Check 4: Form (skeleton, style, altitude)

The cheapest check; do it last and report it briefly.

- **Skeleton.** Leaf files follow the shape (what-it-does, conventions, cross-references); the root file has its maintenance contract; the hub has its module map.
- **Altitude violations.** A fact repeated verbatim across tiers, or module detail that crept into the root file. Flag duplication — each fact should live at one tier.
- **Style.** Backwards-facing language ("now", "currently", "new", "recently"), version markers, references to PRs or tasks, invented-sounding rationale that isn't tied to anything verifiable. Flag these; they're signs of decay.
- **Bloat.** A file that grew long without growing in incidents. Length should track hard-won lessons, not prose.

## Reporting

Lead with the verdict on accuracy — that's what the user is really asking. Structure the report:

1. **Verdict** — one or two sentences: is the system trustworthy right now?
2. **Critical findings** — stale commands, dead references, contradicted invariants. These mislead agents today; fix first.
3. **Discipline signal** — the git analysis, with the K/N number and any doc-only-commit pattern.
4. **Proposed trap entries** — drafted, ready to drop in pending human confirmation. This is the forward-looking value.
5. **Form notes** — brief; skeleton/style/altitude issues.

Then ask before fixing anything. Offer to apply the critical corrections and the confirmed trap entries. The drift fixes and trap drafts are the deliverable; the form notes are housekeeping.

## Judgment calls

- **Don't manufacture findings.** A clean audit is a good outcome. If the files are accurate and the discipline is holding, say so plainly and stop.
- **Distinguish stale-from-neglect from stale-from-youth.** Recently bootstrapped files will have few trap entries and thin rationale — that's correct, not a finding. Judge them on accuracy, not on resemblance to a mature system.
- **A doc that can't go stale may be too vague to be useful.** If nothing in a file is falsifiable, that's worth noting: specificity is what makes a doc valuable, and specificity is what makes it able to drift.
