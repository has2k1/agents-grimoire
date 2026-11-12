---
name: run-trials
description: Run the agents-grimoire behavioural trials (T1 to T5) in the current harness and write a run record. Use after changing either skill's behaviour.
disable-model-invocation: true
---

# Run trials

Run the controlled trial cases against the package's current skills, using
this harness's own way of starting independent agents. You are the
**coordinator**: you build the fixtures, start one **executor** per case,
assess what each executor produced, and write the run record. Executors
exercise the skills; you judge the executors against `evals/expected.json`.

Run every case unless the user names a subset. T5 repeats the bootstrap on
T4's output, so it needs T4 in the same run.

## Executor isolation

Each executor meets the skills as a user's agent would:

- Start it with a clean context: a subagent that inherits none of this
  conversation, or a separate non-interactive session such as `claude -p` or
  `codex exec`, started in the case's fixture.
- Give it the case's `request` text from the run manifest, verbatim, as its
  whole prompt.
- Limit it to its fixture, the pinned skills directory, and its output
  directory. Keep `evals/`, the run directory, and your own notes out of its
  reach.

When the harness cannot provide a clean context, run the case anyway and
record the limit. An executor that has seen the expected outcomes cannot
supply evidence for the skills.

## Steps

1. **Build.** From the package root, choose a new trial root under the
   system temporary directory and a run directory
   `.agents/docs/<YYYYMMDD-HHmm>-trials/run`. Pin the skills, build the
   fixtures, and self-test them:

   ```sh
   mkdir -p "$TRIAL" && cp -R skills "$TRIAL/skills"
   python3 -I evals/build_fixtures.py --trial-root "$TRIAL" \
       --skills "$TRIAL/skills" --run-dir "$RUN"
   python3 -I evals/assess.py --run-dir "$RUN" selftest
   ```

   Done when the self-test exits with status 0.

2. **Run T1 to T4.** Start their executors in parallel. Read each case's
   `workdir`, `output_dir`, and `request` from `$RUN/manifest.json`. Save
   each executor's final reply to `$RUN/transcript-<case>.md`. When an
   executor returns a file's content because its write was blocked, save that
   content verbatim at the requested path and note the transcription for the
   run record. Done when every executor has finished and every requested
   output file exists.

3. **Assess T1 to T4.** Run `python3 -I evals/assess.py --run-dir "$RUN"
   <case>` for each case. Done when `$RUN/assessment-<case>.json` exists for
   each.

4. **Run and assess T5.** Build its fixture with
   `python3 -I evals/build_repeat_fixture.py --run-dir "$RUN"`, then run its
   executor and assess it as in steps 2 and 3.

5. **Review.** Decide every `manual` item and every `should` item that did
   not pass. Use the fixture, the outputs, and the transcripts as evidence,
   and run the fixture's code when an item concerns its behaviour. Classify
   an unexpected finding by its evidence before calling it a false positive.
   Done when every item has a verdict and the evidence behind it.

6. **Record.** Write `validation.md` beside the run directory. Include:

   - the package revision and whether its tree was clean;
   - the pinned skill hashes and ignored instruction files from the manifest;
   - the harness name and version, the model where exposed, the isolation
     method, and any instructions or hooks the executors inherited;
   - each case's outcome, with its automatic check counts and manual verdicts;
   - findings about the skills, with evidence;
   - limits, such as transcribed files, commands outside an executor's
     permitted paths, and cases not run.

   Done when a reader can tell each case's outcome and its evidence from the
   record alone.

Report each case's outcome and the findings to the user. Leave the trial root
in place and name it in the report.
