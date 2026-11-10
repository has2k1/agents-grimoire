# agents-grimoire

Skills for running a **living AGENTS.md documentation system** — the practice
where a repository carries its own agent-facing documentation, keeps it true by
updating it in the same commit as the code it describes, and grows it from real
incidents rather than up-front speculation.

A *grimoire* is a practitioner's working book of hard-won knowledge, passed
between practitioners. That is what a good `AGENTS.md` tree is: not a README
for humans browsing, but the accumulated, maintained knowledge an agent needs
to work in the repo without re-learning every lesson the hard way.

## The system

Three ideas carry the weight:

- **Docs ship with code.** A change that contradicts a documented fact updates
  that file in the *same commit*. Doc-only commits are a smell — they mean the
  doc fell out of the change that made it stale. This is the discipline that
  keeps the files true instead of decaying the way READMEs do.
- **A fact lives at one altitude.** The root file orients, a hub file holds
  cross-cutting rules, and per-module leaf files hold module specifics. Nothing
  is repeated across tiers; the tiers link to each other. The tree shape is
  also an attention budget — an agent working in a module gets that module's
  file injected into context, not the whole tree.
- **Traps are recorded only while they can still bite.** When a bug's fix — or
  a later refactor — removes the condition that made it possible, the trap
  entry is deleted, not annotated. The file describes the code as it *is*; the
  history of the trap lives in git. The ratchet clicks both directions.

## The skills

| Skill | Cadence | What it does |
|---|---|---|
| **`agents-md-bootstrap`** | one-shot | Sets up the three-tier system in a repo that lacks one. Writes only content verifiable from the current code — never invented rationale — and seeds the maintenance contract into the root file so the system is self-sustaining from day one. |
| **`agents-md-audit`** | periodic | Checks the system is still telling the truth: drift between docs and code, the same-commit discipline (via git), whether recent bug fixes earned trap entries and old traps are still reachable, and form. Reports, and drafts fixes and trap entries for human confirmation. |

## Layout

```
agents-grimoire/
├── AGENTS.md                      — agent rules for working in this repo
├── README.md                      — this file
└── skills/
    ├── agents-md-bootstrap/
    │   └── SKILL.md
    └── agents-md-audit/
        └── SKILL.md
```

## Installing

The skills live at <https://github.com/has2k1/agents-grimoire>. Install them
with either skill manager:

```sh
uvx skillmd add has2k1/agents-grimoire
```

```sh
npx skills add has2k1/agents-grimoire
```

Both pull the skills from the repo and place them where your agent harness
reads them, so they track the repo as it evolves.

## Using them

Bootstrap a repo that has no agent docs:

> "Set up an AGENTS.md system in this repo."

Then let the maintenance contract do its work — agents that read the root file
pick up the reflex to keep the docs in the same commit as their changes.

Audit periodically (monthly, or before a release):

> "Are the AGENTS.md files still up to date?"

The audit reports drift and discipline, and proposes trap entries for the bug
fixes that earned them.

## License

MIT — see [LICENSE](LICENSE).
