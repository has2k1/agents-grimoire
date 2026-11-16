# Claude Code executors

Verified with Claude Code 2.1.323 on macOS 27.2, 2026-11-16.

## Trial root

On macOS, choose the trial root under `/private/tmp`, not under `$TMPDIR`.
macOS `mktemp -d` ignores `TMPDIR` and always creates directories in the
per-user temporary directory (`getconf DARWIN_USER_TEMP_DIR`, the usual
`$TMPDIR`). Executors need write access there, and the sandbox cannot
protect a trial root inside a directory it allows writes to: `denyWrite`
also blocks every allowed path beneath it.

## Launch

Start each executor in its fixture, with the manifest's `executor_env`
applied and the case's `request` on stdin:

```sh
cd "$WORKDIR" && env GIT_CONFIG_GLOBAL="$GIT_CONFIG" GIT_PAGER=cat \
  claude -p --bare --no-session-persistence --settings "$SETTINGS" \
    --add-dir "$TRIAL/skills" --add-dir "$OUTDIR" \
    --output-format stream-json --verbose \
    < "$REQUEST" > "$RUN/stream-$CASE.jsonl" 2> "$RUN/stderr-$CASE.txt"
```

- `--bare` skips CLAUDE.md discovery, hooks, auto-memory and plugin sync, so
  the executor inherits none of the user's instructions. It authenticates only
  through `ANTHROPIC_API_KEY`, an `apiKeyHelper` in `--settings`, or a
  third-party provider's own credentials (Bedrock, Vertex, Foundry).
- Pass the request on stdin. `--add-dir` accepts several values and consumes
  a prompt given after it as one more directory.
- Write `$REQUEST` and `$SETTINGS` in the trial root, outside the fixture, so
  the executor's working tree stays as the builder left it.
- Run T1 to T4 as parallel background jobs.

## Settings

Write one settings file per case. Bash runs inside the sandbox, which allows
writes to the working directory (the fixture) and to its own temporary
directory, `/tmp/claude-<uid>`, which it sets as `TMPDIR`. The Read and Edit
tools go through permission rules instead, so deny the protected paths in
both. A `Read` rule covers every file-reading tool; Claude Code warns that
`Glob` and `Grep` rules are never matched. Permission rules write an absolute
path with a leading `//`.

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": ["Bash"],
    "deny": [
      "Read(/<package>/**)", "Edit(/<package>/**)",
      "Read(/<home>/.claude/**)", "Read(/<coordinator-tmp>/**)",
      "Read(/<sibling-root>/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": ["<package>", "<home>/.claude", "<coordinator-tmp>", "<sibling-root>"],
      "allowWrite": ["<output_dir>", "<user-temp>"]
    }
  }
}
```

Replace the placeholders with absolute paths:

| Placeholder | Value |
| --- | --- |
| `<package>` | The package checkout. |
| `<home>` | The user's home directory. |
| `<coordinator-tmp>` | The coordinator's own Claude Code temporary directory, `/private/tmp/claude-$(id -u)/$(pwd \| tr / -)` run from the package root. It holds the coordinator's task output, which executors could otherwise read. |
| `<user-temp>` | `getconf DARWIN_USER_TEMP_DIR` without its trailing slash. |
| `<sibling-root>` | Each other trial root in use at the same time, one entry per root. Executors can list `/private/tmp`, so concurrent roots are otherwise readable. Omit the entry when only one trial root exists. |

## Smoke test

Before the trials, start one executor this way in a throwaway build's T1
fixture. Ask it to run `mktemp -d`, `git status`, and `git check-ignore -v
CLAUDE.md`, to write a file in another fixture, and to read a file in the
package and in the coordinator's temporary directory. Expect `mktemp` and
`git status` to succeed, the ignore rule to come from the generated `ignore`
file, and the write and both reads to be denied. Fix the launch before
running any case when one of these fails.

## Capture

The stream holds one JSON event per line.

- Write the `result` field of the final `"type": "result"` event to
  `$RUN/transcript-<case>.md`.
- Read the model, `claude_code_version`, tools and plugins from the
  `"type": "system", "subtype": "init"` event for the run record.
- Scan the `tool_use` blocks for paths outside the case's permitted
  directories, and the tool results for denials, when recording limits.

## Known artefacts

- Claude Code creates empty `.claude/.cc-writes/` directories in the fixture,
  sometimes in subdirectories too. Git does not track empty directories.
  Record them as harness artefacts rather than executor output.
- The init event lists the user's installed plugins even under `--bare`. Bare
  executors have only the Bash, Edit and Read tools, so they cannot invoke
  plugin skills. Record the list.
- Executors share the sandbox temporary directory `/tmp/claude-<uid>` with
  each other. Record this as an isolation limit.
- A Bash command that names a path under a `Read` deny rule can be refused
  outright ("Permission to use Bash … has been denied") instead of failing
  inside the sandbox with "Operation not permitted". Count both as denials
  when recording limits.
