---
name: agents-md-bootstrap
description: "Bootstrap a hierarchical AGENTS.md system in an established repository that lacks one, or extend it to new modules. Creates the root orientation file, the src/ architecture hub, and per-module leaf files, written ONLY with content verifiable from the current code — never invented rationale or speculative history. Use whenever the user wants to start documenting a repo for AI agents, adopt the AGENTS.md convention, 'set up agent docs', create module-level agent instructions, or bring an undocumented codebase under an AGENTS.md system. Also use when a repo already has a root AGENTS.md but no per-module files and the user wants the full hierarchy."
---

# AGENTS.md Bootstrap

Set up a three-tier AGENTS.md documentation system in a repository that doesn't have one. The system works because an AI agent working in a module gets that module's file injected into context automatically — but only if the files exist and tell the truth. Everything you write must be **verifiable from the code as it exists right now**, because the single worst outcome is a confident, plausible file that describes a system the code doesn't actually have.

The temptation to resist: established repos invite you to *explain* the design. Don't. A bootstrap has no access to why decisions were made — that history lives in the team's heads and commit messages, and guessing at it produces fiction that reads exactly like fact. What you can truthfully document is **what the code is**: its surfaces, its commands, its load-bearing invariants. Rationale gets added later, by the team, as real decisions and real bugs occur. Thin and true beats comprehensive and false.

## The three tiers

You are building a tree, not a document. Each tier has one job and one altitude, and a fact lives at exactly one tier with links to the others.

| Tier | File | Job | Content |
|---|---|---|---|
| 1. Root | `AGENTS.md` | Orientation | Pitch, verifiable commands, style rules, the maintenance contract, "where to look next" index |
| 2. Hub | one per source root (e.g. `src/AGENTS.md`) | Cross-cutting architecture | Invariants no single module owns + the module map |
| 3. Leaf | one per module/package/directory | Module specifics | Surface, conventions, cross-references |

Not every repo needs all three tiers. A small repo may need only tier 1 plus a few leaf files. Create a hub file only if there are genuinely cross-cutting rules that no single module owns — don't manufacture one to fill the pattern.

## Process

### 1. Survey before writing anything

Map the repository structure and identify the natural module boundaries — the directories or packages an agent would work within. For each candidate module, read enough of the actual code to state its surface truthfully. Look for:

- **The real commands.** Build, test, lint, format, run — from `package.json`, `Cargo.toml`, `Makefile`, `pyproject.toml`, CI config, README. Only include a command if you can see it's real. Run it if feasible.
- **The hard invariants.** The rules that, if broken, break the system. You find these in: type constraints, exhaustive-match requirements, registration patterns ("every X must also register a Y"), shared enums that must stay in sync, tests that pin a convention. These are gold — they're exactly what an agent needs and exactly what a newcomer breaks.
- **The module dependency shape.** What may depend on what. Look for layering rules enforced in code or imports.

### 2. Write the root file

Structure:

```markdown
# AGENTS.md

<One-paragraph pitch: what the project is, the design driver, what must work.>

## Commands
<Table or code block of commands, each with an inline comment saying what it
proves — not what it does. `cargo check --target wasm32  # wasm is a supported
target; catches GL-backend regressions`, not `# build wasm`.>

## <Style rules, only if the project has them written down or clearly enforceable>

## The maintenance contract
<See below — this section is mandatory.>

## Where to look next
<The index: one line per hub/leaf file, saying what each contains.>
```

**The maintenance contract is non-negotiable and goes verbatim in the root file.** It is what makes the system self-sustaining: it instructs every future agent, at the moment it reads the file, to keep the docs true. Write it as a short section like:

> ## Maintaining these files
>
> These AGENTS.md files describe how the code *is*. When you change behavior that a file documents — a command, a surface, an invariant, a module boundary — update that file in the **same commit** as the code change, not as a follow-up. A doc-only commit is a smell: it means the doc fell out of the change that made it stale. If a change contradicts a documented rule and the change is intentional, the rule was wrong — rewrite it, don't leave it standing.
>
> Keep each fact at one altitude: root orients, the hub holds cross-cutting rules, module files hold module specifics. Link between tiers; never repeat a fact across them.
>
> When you fix a bug whose diagnosis took real effort, add a short entry to the relevant module file recording the symptom, the mechanism, and how to recognize it — that is how these files grow. Add it only while the failure can still recur: if the fix, or a later refactor, removed the condition that made the bug possible, the entry guards nothing and should not be written — or, if already written, deleted rather than annotated. A trap entry's job is to stop the next agent falling into a hole that still exists; one that survives its own hole teaches a false belief about how the code behaves. When a new abstraction is what makes a bug shallow but the abstraction can be bypassed, record the guardrail instead ("use X, don't do Y — Y is what caused this") so the entry defends the thing that prevents the bug.

Without this section, you've produced files that start decaying the day you write them. With it, every harness that injects the root file also injects the reflex to maintain it.

### 3. Write the hub file (if warranted)

Only cross-cutting content. The test for "belongs here": *would deleting this let two modules drift into inconsistent behavior?* Include the module map — one line per module, each naming its leaf file.

### 4. Write leaf files

One per module, and **sparse**. Fill only what you can verify:

```markdown
# <path>/AGENTS.md

<One sentence: what this module is.> See <upward link> for <the rule it lives under>.

## What this module does
<Its place in the system and its public surface — verifiable from the code.>

## Conventions
<Load-bearing, non-obvious rules, imperative + reason. ONLY ones you can see
enforced in the code. If none are visible, omit the section.>

## Cross-references
<Downward/sideways links, one line each.>
```

It is correct and healthy for a leaf file to be short. Do not pad. If you cannot verify a convention, leave it out — the team adds it when it bites.

## What to exclude

- **No invented rationale.** "Why" sections, design histories, rejected alternatives — all off-limits in a bootstrap, because you'd be guessing. The one exception: rationale that is *written down in the code or README* and that you can point to.
- **No speculative commands.** Every command must exist in config or be runnable.
- **No backwards-facing language.** No "now", "currently", "new", "recently". Describe present behavior only.
- **No version markers or task references** in the files.
- **Don't document what the code makes obvious.** The value is invariants and surfaces, not restating that a file named `parser.rs` parses.

## Finishing up

Report: how many files created, at which tiers, and — most useful — a short list of the load-bearing invariants you found that the team should confirm you got right. Those invariants are the highest-risk content (they look like fact) and the highest-value (they're what agents break), so flag them for human review explicitly.
