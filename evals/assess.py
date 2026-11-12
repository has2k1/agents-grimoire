"""
Assess finished behavioural-trial runs against the expected outcomes

The run directory holds the manifest that `build_fixtures.py` wrote and, for
T5, the record that `build_repeat_fixture.py` wrote. Expected outcomes come
from `expected.json` beside this script. Run from the package root::

    python3 -I evals/assess.py --run-dir /tmp/grimoire-evals-run selftest
    python3 -I evals/assess.py --run-dir /tmp/grimoire-evals-run T1

`selftest` confirms, before any executor runs, that each fixture's
checkpoint-like commits have their intended status. A case name checks that
case's fixture and outputs and writes `assessment-<case>.json` to the run
directory.

Each check has a level: `must` failures fail the case, `should` failures are
reported for review, `manual` items need a reviewer, and `info` results do not
affect the outcome. A case passes mechanically only when no `must` check
fails; findings quality, evidence and rationale still need the manual review
listed in the result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, TypeAlias

# A decoded JSON object, such as the run manifest or an expected outcome.
JsonObject: TypeAlias = dict[str, Any]

EVALS = Path(__file__).resolve().parent
SUBJECT = "chore: record agent documentation audit"
TRAILER_KEYS = [
    "Agents-Audit-Version",
    "Agents-Audit-Commit",
    "Agents-Audit-Tree",
    "Agents-Audit-Skill-Revision",
    "Agents-Audit-Previous",
]
HEADINGS = [
    "Coverage",
    "Unverified checks",
    "New findings",
    "Carried findings",
    "Closed findings",
]
INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md", "AGENTS.override.md", "CLAUDE.local.md"}
CACHE_PARTS = {"__pycache__", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
ID_TOKEN = re.compile(r"\b(?:[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+|[A-Z]{1,4}-?\d+)\b")
NOT_IDS = {"SHA-1", "SHA-256", "UTF-8", "ISO-8601", "RFC-3339", "PEP-8"}


def use_trial_root(trial_root: Path) -> None:
    """
    Point this process's Git inspections at the trial root's empty configuration

    Inspection must ignore the same user-wide rules as the build, or
    `git status --ignored` would differ from the recorded before-state. Every
    Git command inherits `XDG_CONFIG_HOME` from this process's environment.
    """
    config_home = trial_root / "builder-xdg-empty"
    config_home.mkdir(parents=True, exist_ok=True)
    os.environ["XDG_CONFIG_HOME"] = str(config_home)


def resolve(info: JsonObject, label: str) -> str:
    """
    Return the commit SHA that an expected-outcome label names

    Parameters
    ----------
    info
        The case's entry in the run manifest.
    label
        A key of the case's `commits`, or `none`, which is returned unchanged.
    """
    if label == "none":
        return label
    try:
        return str(info["commits"][label])
    except KeyError:
        sys.exit(f"expected.json names unknown commit label {label!r}")


# State capture, kept identical to the builders ------------------------------


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of the file at `path`"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def base_env() -> dict[str, str]:
    """Return the isolated Git environment used to inspect fixtures"""
    env = dict(os.environ)
    env.update(
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_OPTIONAL_LOCKS="0",
        LC_ALL="C",
        TZ="UTC",
    )
    return env


def git(repo: Path, *args: str, stdin: str | None = None, check: bool = True) -> str:
    """Run a read-only Git command in `repo` and return its standard output"""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=base_env(),
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def snapshot(repo: Path) -> JsonObject:
    """Capture the repository state that a read-only run must preserve"""
    index = (repo / ".git/index").read_bytes()
    files = {}
    for path in sorted(repo.rglob("*")):
        rel = path.relative_to(repo)
        if rel.parts[0] == ".git" or path.is_dir():
            continue
        files[str(rel)] = {
            "sha256": sha256_file(path),
            "mode": oct(path.stat().st_mode & 0o777),
        }
    return {
        "head": git(repo, "rev-parse", "HEAD").strip(),
        "head_tree": git(repo, "rev-parse", "HEAD^{tree}").strip(),
        "head_ref": git(repo, "symbolic-ref", "-q", "HEAD").strip(),
        "status_porcelain_v2": git(
            repo, "status", "--porcelain=v2", "--untracked-files=all"
        ),
        "status_ignored": git(
            repo, "status", "--porcelain=v2", "--ignored", "--untracked-files=all"
        ),
        "index_sha1": hashlib.sha1(index).hexdigest(),
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "ls_files_stage": git(repo, "ls-files", "-s"),
        "staged_diff_sha256": hashlib.sha256(
            git(repo, "diff", "--cached", "--binary").encode()
        ).hexdigest(),
        "refs": git(repo, "for-each-ref", "--format=%(objectname) %(refname)"),
        "local_config": git(repo, "config", "--local", "--list"),
        "commit_count": git(repo, "rev-list", "--count", "--all").strip(),
        "files": files,
    }


# Message parsing ----------------------------------------------------------


def trailers(message: str) -> list[tuple[str, str]]:
    """Return the message's trailers in order, as Git parses them"""
    parsed = subprocess.run(
        ["git", "interpret-trailers", "--parse"],
        input=message,
        capture_output=True,
        text=True,
        env=base_env(),
        check=True,
    ).stdout
    pairs = []
    for line in parsed.splitlines():
        key, _, value = line.partition(":")
        pairs.append((key.strip(), value.strip()))
    return pairs


def sections(message: str) -> dict[str, str]:
    """Return the text under each `##` heading, stopping at the trailers"""
    result: dict[str, list[str]] = {}
    current = None
    for line in message.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        elif line.startswith("Agents-Audit-"):
            current = None
        elif current is not None:
            result[current].append(line)
    return {key: "\n".join(value).strip() for key, value in result.items()}


def heading_order(message: str) -> list[str]:
    """Return the `##` headings of `message` in order"""
    return [line[3:].strip() for line in message.splitlines() if line.startswith("## ")]


def is_none(text: str) -> bool:
    """Report whether a section body states that it is empty"""
    return text.strip().strip("_*").rstrip(".").strip() == "None"


def id_tokens(text: str) -> set[str]:
    """Return tokens in `text` that look like finding IDs"""
    return {
        t
        for t in ID_TOKEN.findall(text)
        if any(c.isdigit() for c in t) and t not in NOT_IDS
    }


def finding_block(section: str, finding: str) -> str | None:
    """
    Return the lines describing `finding` within one report section

    A block starts at the first line naming the ID and ends before a line that
    begins, after list or emphasis markup, with a different ID.
    """
    lines = section.splitlines()
    start = next((i for i, line in enumerate(lines) if finding in line), None)
    if start is None:
        return None
    lead = re.compile(
        r"^\s*(?:[-*+]|\d+\.)?\s*(?:#+\s*)?[*_`\[]*\s*(" + ID_TOKEN.pattern + r")"
    )
    block = [lines[start]]
    for line in lines[start + 1 :]:
        match = lead.match(line)
        if match and match.group(1) != finding and match.group(1) not in NOT_IDS:
            break
        block.append(line)
    return "\n".join(block)


def sha_reference(text: str, sha: str) -> str:
    """Classify how `text` refers to commit `sha`: full, abbreviated or absent"""
    if sha in text:
        return "full"
    if re.search(r"\b" + sha[:7] + r"[0-9a-f]*\b", text):
        return "abbreviated"
    return "absent"


# Checkpoint conditions ----------------------------------------------------


def checkpoint_reasons(
    repo: Path, sha: str, target: str, cache: dict[str, list[str]]
) -> list[str]:
    """
    Return the checkpoint conditions that commit `sha` fails

    The conditions follow the audit skill's baseline selection: complete
    trailers, one parent matching the recorded commit and tree, first-parent
    reachability, a valid nearest predecessor, all report sections, and
    reconciliation of every open predecessor finding. An empty list means
    `sha` is a checkpoint.
    """
    if sha in cache:
        return cache[sha]
    reasons: list[str] = []
    message = git(repo, "show", "-s", "--format=%B", sha)
    pairs = trailers(message)
    values: dict[str, list[str]] = {}
    for key, value in pairs:
        values.setdefault(key, []).append(value)
    for key in TRAILER_KEYS:
        if len(set(values.get(key, []))) != 1:
            reasons.append(f"trailer {key} missing or conflicting")
    if values.get("Agents-Audit-Version", [""])[0] != "1":
        reasons.append("unsupported version")
    parents = git(repo, "show", "-s", "--format=%P", sha).split()
    tree = git(repo, "rev-parse", f"{sha}^{{tree}}").strip()
    if len(parents) != 1:
        reasons.append("not exactly one parent")
    else:
        parent = parents[0]
        if values.get("Agents-Audit-Commit", [""])[0] != parent:
            reasons.append("Agents-Audit-Commit differs from the parent")
        recorded_tree = values.get("Agents-Audit-Tree", [""])[0]
        if (
            git(repo, "rev-parse", f"{parent}^{{tree}}").strip() != recorded_tree
            or tree != recorded_tree
        ):
            reasons.append("parent or commit tree differs from Agents-Audit-Tree")
        if sha not in git(repo, "rev-list", "--first-parent", target).split():
            reasons.append("not on the target's first-parent history")
        previous = values.get("Agents-Audit-Previous", [""])[0]
        earlier = git(
            repo,
            "log",
            "--first-parent",
            "--format=%H",
            "--grep=^Agents-Audit-Version: 1$",
            parent,
        ).split()
        nearest = next(
            (c for c in earlier if not checkpoint_reasons(repo, c, target, cache)),
            "none",
        )
        if previous != nearest:
            reasons.append(
                f"Agents-Audit-Previous {previous} is not the nearest checkpoint {nearest}"
            )
        body = sections(message)
        if [h for h in HEADINGS if h not in body] or not body.get("Coverage"):
            reasons.append("report sections or coverage missing")
        if previous not in ("none", "") and previous == nearest:
            earlier_body = sections(git(repo, "show", "-s", "--format=%B", previous))
            open_ids = id_tokens(earlier_body.get("New findings", "")) | id_tokens(
                earlier_body.get("Carried findings", "")
            )
            accounted = id_tokens(body.get("Carried findings", "")) | id_tokens(
                body.get("Closed findings", "")
            )
            if open_ids - accounted:
                reasons.append(
                    f"open predecessor findings unaccounted: {sorted(open_ids - accounted)}"
                )
    cache[sha] = reasons
    return reasons


def selftest(manifest: JsonObject, expected: JsonObject) -> JsonObject:
    """Check that each fixture's checkpoint-like commits have the intended status"""
    out: JsonObject = {}
    for case, valid, invalid in [
        ("T1", ["C1", "C2"], []),
        ("T2", ["C1"], ["X"]),
        ("T3", [], []),
        ("T4", [], []),
    ]:
        info = manifest["cases"][case]
        repo = Path(info["fixture"])
        cache: dict[str, list[str]] = {}
        found = git(
            repo,
            "log",
            "--first-parent",
            "--format=%H",
            "--grep=^Agents-Audit-Version: 1$",
            "HEAD",
        ).split()
        for sha in reversed(found):
            checkpoint_reasons(repo, sha, "HEAD", cache)
        nearest = next((c for c in found if not cache[c]), "none")
        result = {"candidates": {sha: cache[sha] for sha in found}, "baseline": nearest}
        assert sorted(found) == sorted(info["commits"][k] for k in valid + invalid), (
            case
        )
        for label in valid:
            assert cache[info["commits"][label]] == [], (
                case,
                label,
                cache[info["commits"][label]],
            )
        for label in invalid:
            assert cache[info["commits"][label]], (case, label)
        out[case] = result
    cases = manifest["cases"]
    for case in ("T1", "T2"):
        assert out[case]["baseline"] == resolve(
            cases[case], expected[case]["baseline"]
        ), case
    x = resolve(cases["T2"], expected["T2"]["not_checkpoint"])
    assert out["T2"]["candidates"][x] == ["Agents-Audit-Commit differs from the parent"]
    return out


# Checks -------------------------------------------------------------------


class Checks:
    """The ordered check results for one case"""

    def __init__(self) -> None:
        self.items: list[JsonObject] = []

    def add(
        self, name: str, level: str, ok: bool | None, detail: object = None
    ) -> None:
        """Record one check; `ok=None` marks a result that needs review"""
        status = "pass" if ok else ("review" if ok is None else "fail")
        self.items.append(
            {"check": name, "level": level, "status": status, "detail": detail}
        )

    def outcome(self) -> str:
        """Return `failed`, `review` or `passed` for the recorded checks"""
        if any(i["status"] == "fail" and i["level"] == "must" for i in self.items):
            return "failed"
        if any(i["status"] != "pass" and i["level"] != "info" for i in self.items):
            return "review"
        return "passed"


def compare_state(before: JsonObject, after: JsonObject) -> JsonObject:
    """Return the differences between two snapshots, by field"""
    diff: JsonObject = {}
    for key, value in before.items():
        if key != "files" and value != after[key]:
            diff[key] = {"before": value, "after": after[key]}
    old, new = before["files"], after["files"]
    files = {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": sorted(k for k in set(old) & set(new) if old[k] != new[k]),
    }
    if any(files.values()):
        diff["files"] = files
    return diff


def check_trailers(
    checks: Checks, message: str, expect: dict[str, str], audit_sha: str
) -> None:
    """Check that `message` has exactly the five trailers with the expected values"""
    pairs = trailers(message)
    audit_keys = [k for k, _ in pairs if k.startswith("Agents-Audit-")]
    checks.add(
        "exactly five Agents-Audit trailers, each once",
        "must",
        sorted(audit_keys) == sorted(TRAILER_KEYS),
        audit_keys,
    )
    values = dict(pairs)
    for key, want in expect.items():
        checks.add(f"{key} = {want}", "must", values.get(key) == want, values.get(key))
    revision = values.get("Agents-Audit-Skill-Revision", "")
    checks.add(
        "Skill-Revision identifies the pinned audit skill",
        "should",
        True if audit_sha in revision else (None if revision else False),
        revision,
    )


def check_message_shape(checks: Checks, message: str) -> None:
    """Check the subject line and the order of the `##` report headings"""
    checks.add(
        "subject line",
        "must",
        message.splitlines()[:1] == [SUBJECT],
        message.splitlines()[:1],
    )
    checks.add(
        "five ## headings in template order",
        "must",
        heading_order(message) == HEADINGS,
        heading_order(message),
    )


def present(body: dict[str, str], finding: str) -> list[str]:
    """Return the finding sections that mention `finding`"""
    return [h for h in HEADINGS[2:] if finding in body.get(h, "")]


def check_carried(
    checks: Checks, body: dict[str, str], item: dict[str, str], other: list[str]
) -> None:
    """Check that a finding is carried with its source checkpoint"""
    finding = item["id"]
    checks.add(
        f"{finding} only under Carried findings",
        "must",
        present(body, finding) == ["Carried findings"],
        present(body, finding),
    )
    block = finding_block(body.get("Carried findings", ""), finding) or ""
    ref = sha_reference(block, item["source_checkpoint"])
    checks.add(
        f"{finding} names source checkpoint {item['source_checkpoint']}",
        "must",
        True if ref == "full" else (None if ref == "abbreviated" else False),
        ref,
    )
    for sha in other:
        if sha_reference(block, sha) != "absent":
            checks.add(
                f"{finding} block also names {sha}; confirm it is not given as the source",
                "manual",
                None,
            )
    checks.add(
        f"{finding} block mentions {item['subject']}",
        "should",
        item["subject"] in block,
    )


def audit_output(info: JsonObject) -> tuple[Path, str | None]:
    """Return the output directory and the proposed checkpoint message, if written"""
    out = Path(info["output_dir"])
    path = out / "checkpoint-message.txt"
    return out, path.read_text(encoding="utf-8") if path.exists() else None


def assess_read_only(checks: Checks, info: JsonObject) -> None:
    """Check that a read-only run left the fixture exactly as recorded"""
    repo = Path(info["fixture"])
    diff = compare_state(info["before"], snapshot(repo))
    caches = [
        p
        for p in diff.get("files", {}).get("added", [])
        if CACHE_PARTS & set(Path(p).parts)
    ]
    checks.add(
        "repository unchanged (HEAD, refs, index bytes, entries, status, config, files)",
        "must",
        not diff,
        diff or None,
    )
    if caches:
        checks.add("unchanged state violated only by caches?", "manual", None, caches)


def assess_t1_t2(
    case: str, manifest: JsonObject, expected: JsonObject, audit_sha: str
) -> Checks:
    """Assess a read-only audit run against its expectations"""
    checks = Checks()
    info = manifest["cases"][case]
    want = expected[case]
    out, message = audit_output(info)
    checks.add("report.md written", "should", (out / "report.md").exists())
    checks.add("checkpoint-message.txt written", "must", message is not None)
    assess_read_only(checks, info)
    if message is None:
        return checks
    check_message_shape(checks, message)
    check_trailers(
        checks,
        message,
        {
            "Agents-Audit-Version": "1",
            "Agents-Audit-Commit": resolve(info, want["commit"]),
            "Agents-Audit-Tree": info["before"]["head_tree"],
            "Agents-Audit-Previous": resolve(info, want["previous"]),
        },
        audit_sha,
    )
    body = sections(message)
    report_path = out / "report.md"
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else None
    checks.add(
        "Coverage names the baseline as history boundary",
        "should",
        sha_reference(body.get("Coverage", ""), resolve(info, want["baseline"]))
        == "full",
    )
    commits = info["commits"]
    for item in want["carried"]:
        item = {**item, "source_checkpoint": resolve(info, item["source_checkpoint"])}
        others = [
            v
            for k, v in commits.items()
            if k.startswith("C") and v != item["source_checkpoint"]
        ]
        check_carried(checks, body, item, others)
    for item in want.get("closed", []):
        finding = item["id"]
        checks.add(
            f"{finding} only under Closed findings",
            "must",
            present(body, finding) == ["Closed findings"],
            present(body, finding),
        )
    for finding in want.get("absent_everywhere", []):
        checks.add(
            f"{finding} absent from finding sections",
            "must",
            present(body, finding) == [],
            present(body, finding),
        )
    for finding in want.get("not_closed", []):
        checks.add(
            f"{finding} not closed",
            "must",
            "Closed findings" not in present(body, finding),
        )
    new = body.get("New findings", "")
    if case == "T1":
        spec = want["new"]
        fresh = id_tokens(new) - set(spec["fresh_id_not_in"])
        checks.add("New findings not empty", "must", not is_none(new))
        checks.add(
            "New findings reuse no earlier ID",
            "must",
            not (id_tokens(new) & set(spec["fresh_id_not_in"])),
            sorted(id_tokens(new)),
        )
        checks.add(
            "New findings carry a fresh ID",
            "must",
            True if len(fresh) == 1 else (None if fresh else False),
            sorted(fresh),
        )
        for term in spec["subject_terms_all"]:
            checks.add(f"New findings mention {term}", "must", term in new)
        for term in spec["subject_terms_should"]:
            checks.add(f"New findings mention {term}", "should", term in new)
    if case == "T2":
        bogus = want["bogus"]
        checks.add(
            f"bogus {bogus} not carried",
            "must",
            "Carried findings" not in present(body, bogus),
        )
        checks.add(
            f"bogus {bogus} not new", "must", "New findings" not in present(body, bogus)
        )
        checks.add(
            f"bogus {bogus} not closed",
            "should",
            "Closed findings" not in present(body, bogus),
        )
        for term in want["new_must_not_mention"]:
            checks.add(f"New findings do not mention {term}", "must", term not in new)
        checks.add(
            "New findings None",
            "should",
            True if is_none(new) else None,
            None if is_none(new) else new,
        )
        # A commit failing the checkpoint conditions is an ordinary commit.
        # Listing it, even as a rejected candidate, presents it as a checkpoint.
        x = resolve(info, want["not_checkpoint"])
        texts = {"checkpoint-message.txt": message, "report.md": report}
        for name, level in want["not_checkpoint_absent"].items():
            text = texts[name]
            ok = None if text is None else sha_reference(text, x) == "absent"
            checks.add(
                f"{want['not_checkpoint']} ({x[:7]}) absent from {name}",
                level,
                ok,
                None if text is not None else "file not written",
            )
    for item in want["manual"]:
        checks.add(item, "manual", None)
    return checks


def assess_t3(manifest: JsonObject, expected: JsonObject, audit_sha: str) -> Checks:
    """Assess the authorised checkpoint creation run"""
    checks = Checks()
    info = manifest["cases"]["T3"]
    want = expected["T3"]
    repo = Path(info["fixture"])
    before = info["before"]
    parent = resolve(info, want["parent"])
    after = snapshot(repo)
    head = after["head"]
    parents = git(repo, "show", "-s", "--format=%P", head).split()
    checks.add(
        "one new commit",
        "must",
        int(after["commit_count"]) == int(before["commit_count"]) + 1,
        [before["commit_count"], after["commit_count"]],
    )
    checks.add("sole parent is the prior HEAD", "must", parents == [parent], parents)
    checks.add(
        "commit tree equals parent tree",
        "must",
        after["head_tree"] == before["head_tree"],
        after["head_tree"],
    )

    def other_refs(refs: str) -> list[str]:
        """Return the refs other than `refs/heads/main`"""
        return [r for r in refs.splitlines() if not r.endswith(" refs/heads/main")]

    checks.add(
        "no other ref changed",
        "must",
        other_refs(before["refs"]) == other_refs(after["refs"]),
    )
    checks.add(
        "HEAD still on refs/heads/main", "must", after["head_ref"] == "refs/heads/main"
    )
    checks.add(
        "index entries unchanged",
        "must",
        before["ls_files_stage"] == after["ls_files_stage"],
    )
    checks.add(
        "staged diff unchanged",
        "must",
        before["staged_diff_sha256"] == after["staged_diff_sha256"],
    )
    checks.add(
        "status unchanged",
        "must",
        before["status_porcelain_v2"] == after["status_porcelain_v2"],
        after["status_porcelain_v2"],
    )
    checks.add(
        "worktree files unchanged, including the untracked file",
        "must",
        before["files"] == after["files"],
        compare_state(before, after).get("files"),
    )
    checks.add(
        "local config unchanged",
        "should",
        before["local_config"] == after["local_config"],
    )
    checks.add(
        "raw index bytes unchanged (Git may rewrite stat data)",
        "info",
        True if before["index_sha256"] == after["index_sha256"] else None,
    )
    raw = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "commit", head],
        env=base_env(),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    stored = raw.split("\n\n", 1)[1]
    check_message_shape(checks, stored)
    check_trailers(
        checks,
        stored,
        {
            "Agents-Audit-Version": "1",
            "Agents-Audit-Commit": parent,
            "Agents-Audit-Tree": before["head_tree"],
            "Agents-Audit-Previous": want["previous"],
        },
        audit_sha,
    )
    body = sections(stored)
    checks.add("every section has content", "must", all(body.get(h) for h in HEADINGS))
    new = body.get("New findings", "")
    checks.add(
        "New findings None",
        "should",
        True if is_none(new) else None,
        None if is_none(new) else new,
    )
    _, authored = audit_output(info)
    checks.add(
        "stored message equals authored message file byte for byte",
        "should",
        True if authored == stored else (None if authored is None else False),
    )
    with tempfile.TemporaryDirectory(
        prefix="t3-clone-", dir=manifest["trial_root"]
    ) as tmp:
        clone = Path(tmp) / "clone"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-local", str(repo), str(clone)],
            env=base_env(),
            check=True,
            capture_output=True,
        )
        cloned = subprocess.run(
            ["git", "-C", str(clone), "cat-file", "commit", "HEAD"],
            env=base_env(),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split("\n\n", 1)[1]
        recovered = cloned == stored and heading_order(cloned) == HEADINGS
        checks.add("fresh clone recovers the full report", "must", recovered)
    for item in want["manual"]:
        checks.add(item, "manual", None)
    return checks


def instruction_files(repo: Path) -> list[Path]:
    """Return instruction files in the worktree, including `@` imports from CLAUDE.md files"""
    found = {
        p
        for p in repo.rglob("*.md")
        if ".git" not in p.relative_to(repo).parts
        and (p.name in INSTRUCTION_NAMES or ".claude" in p.relative_to(repo).parts)
    }
    for path in list(found):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("@"):
                target = (path.parent / line[1:].strip()).resolve()
                if target.is_file() and target.is_relative_to(repo.resolve()):
                    found.add(target)
    return sorted(found)


def normalise(text: str) -> str:
    """Collapse whitespace so wrapped text compares equal"""
    return " ".join(text.split())


def contract_paragraphs(manifest: JsonObject) -> list[str]:
    """Return the paragraphs of the pinned bootstrap skill's maintenance contract"""
    skill = Path(manifest["skills"]["agents-md-bootstrap"]["path"])
    lines = skill.read_text(encoding="utf-8").splitlines()
    start = lines.index("> ## Maintaining these files")
    block = []
    for line in lines[start:]:
        if not line.startswith(">"):
            break
        block.append(line[2:] if line.startswith("> ") else "")
    return [normalise(p) for p in "\n".join(block).split("\n\n") if p.strip()]


def check_bootstrap_content(
    checks: Checks, repo: Path, want: JsonObject, manifest: JsonObject
) -> None:
    """Check policy preservation, the maintenance contract and history-only rationale"""
    files = instruction_files(repo)
    texts = {
        str(p.relative_to(repo.resolve()) if p.is_absolute() else p): p.read_text(
            encoding="utf-8"
        )
        for p in (f.resolve() for f in files)
    }
    combined = normalise("\n".join(texts.values()))
    checks.add("instruction files found", "should", bool(texts), sorted(texts))
    checks.add(
        "release policy preserved verbatim",
        "must",
        normalise(want["policy"]) in combined,
    )
    heading = re.compile(r"^#+\s+Maintaining these files\s*$", re.MULTILINE)
    count = sum(
        len(heading.findall(p.read_text(encoding="utf-8")))
        for p in repo.rglob("*.md")
        if ".git" not in p.relative_to(repo).parts
    )
    checks.add(
        "exactly one maintenance contract heading across all Markdown",
        "must",
        count == want["contract_count"],
        count,
    )
    paragraphs = contract_paragraphs(manifest)
    verbatim = normalise("\n\n".join(paragraphs)) in combined
    missing = [p[:60] for p in paragraphs[1:] if p not in combined]
    checks.add(
        "maintenance contract verbatim",
        "should",
        True if verbatim else None,
        None if verbatim else {"paragraphs_not_verbatim": missing},
    )
    for term in want["history_only_rationale_absent"]:
        checks.add(
            f"history-only rationale '{term}' absent",
            "must",
            term.lower() not in combined.lower(),
        )
    unresolved = []
    for rel, text in texts.items():
        for token in re.findall(r"`([^`\s]+)`", text):
            if (
                "/" in token or re.search(r"\.(md|py|toml|sh|txt)$", token)
            ) and not token.startswith(("-", "http")):
                candidate = token.rstrip("/").split("::")[0]
                if not (
                    (repo / candidate).exists()
                    or (repo / Path(rel).parent / candidate).exists()
                ):
                    unresolved.append(f"{rel}: {token}")
    checks.add(
        "backticked paths resolve",
        "should",
        True if not unresolved else None,
        unresolved or None,
    )


def assess_bootstrap(
    case: str,
    before: JsonObject,
    expected: JsonObject,
    manifest: JsonObject,
    run_dir: Path,
) -> Checks:
    """
    Assess an initial or repeat bootstrap run

    Parameters
    ----------
    case
        `T4` or `T5`.
    before
        The case record holding the fixture, output directory and before-state.
    expected
        The expected outcomes of every case.
    manifest
        The run manifest, which names the pinned bootstrap skill.
    run_dir
        The directory receiving the T5 diff listing.
    """
    checks = Checks()
    want = expected[case]
    repo = Path(before["fixture"])
    state = snapshot(repo)
    diff = compare_state(before["before"], state)
    files = diff.get("files", {"added": [], "removed": [], "changed": []})
    touched = files["added"] + files["removed"] + files["changed"]
    non_instruction = [
        p
        for p in touched
        if Path(p).name not in INSTRUCTION_NAMES and ".claude" not in Path(p).parts
    ]
    checks.add(
        "handoff report written",
        "should",
        (Path(before["output_dir"]) / "report.md").exists(),
    )
    checks.add(
        "only instruction files touched",
        "must",
        not non_instruction,
        non_instruction or None,
    )
    checks.add(
        "HEAD and refs unchanged",
        "should",
        state["head"] == before["before"]["head"]
        and state["refs"] == before["before"]["refs"],
    )
    checks.add(
        "index entries unchanged",
        "should",
        state["ls_files_stage"] == before["before"]["ls_files_stage"],
    )
    if case == "T4":
        checks.add("CLAUDE.md kept", "should", (repo / "CLAUDE.md").is_file())
        checks.add("instruction files changed", "should", bool(touched), touched)
    else:
        checks.add(
            "no diff on repeat run",
            "should",
            True if not touched else None,
            touched or None,
        )
        if touched:
            listing = (
                git(repo, "diff", "--no-color")
                + "\n# untracked or ignored\n"
                + "\n".join(files["added"])
            )
            (run_dir / "assessment-T5-diff.txt").write_text(listing)
    check_bootstrap_content(checks, repo, want, manifest)
    checks.add(
        "file differences",
        "manual" if touched else "info",
        None if touched else True,
        files,
    )
    for item in want["manual"]:
        checks.add(item, "manual", None)
    return checks


def parse_args() -> argparse.Namespace:
    """Parse the run directory and the case to assess"""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="run directory holding manifest.json and receiving assessments",
    )
    parser.add_argument("case", choices=["selftest", "T1", "T2", "T3", "T4", "T5"])
    return parser.parse_args()


def main() -> None:
    """Assess one case, or self-test the fixtures, and print the result"""
    args = parse_args()
    run_dir = args.run_dir.absolute()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    expected = json.loads((EVALS / "expected.json").read_text(encoding="utf-8"))
    use_trial_root(Path(manifest["trial_root"]))
    if args.case == "selftest":
        print(json.dumps(selftest(manifest, expected), indent=2))
        return
    for name, info in manifest["skills"].items():
        if sha256_file(Path(info["path"])) != info["sha256"]:
            sys.exit(f"pinned skill {name} changed since the build: {info['path']}")
    audit_sha = manifest["skills"]["agents-md-audit"]["sha256"]
    case = args.case
    if case in ("T1", "T2"):
        checks = assess_t1_t2(case, manifest, expected, audit_sha)
    elif case == "T3":
        checks = assess_t3(manifest, expected, audit_sha)
    elif case == "T4":
        checks = assess_bootstrap(
            "T4", manifest["cases"]["T4"], expected, manifest, run_dir
        )
    else:
        record = json.loads((run_dir / "manifest-T5.json").read_text(encoding="utf-8"))
        checks = assess_bootstrap("T5", record, expected, manifest, run_dir)
    result = {"case": case, "outcome": checks.outcome(), "checks": checks.items}
    (run_dir / f"assessment-{case}.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
