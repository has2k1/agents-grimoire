r"""
Build the disposable fixture repositories T1 to T4 for the behavioural trials

Each fixture is a small Git repository with a fixed identity and fixed dates.
Rebuilding with the same pinned skills, Git version and platform reproduces
every commit SHA. The checkpoint fixtures embed the audit skill's content hash
and T3 quotes the bootstrap skill's maintenance contract, so their SHAs change
when those skills change.

The trial root receives the fixtures, an empty output directory per case and
an empty Git configuration directory. The run directory receives the run
manifest, the fixture bundles and the authored checkpoint messages. The trial
root and the pinned skills must lie outside this package, and the run
directory outside its `evals/` and `skills/` directories, so executors cannot
reach the expected outcomes. Existing fixtures are never replaced.

Run from the package root, for example::

    python3 -I evals/build_fixtures.py --trial-root /tmp/grimoire-evals \
        --skills /tmp/grimoire-evals/skills --run-dir /tmp/grimoire-evals-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias

# A decoded JSON object, such as the run manifest.
JsonObject: TypeAlias = dict[str, Any]

EVALS = Path(__file__).resolve().parent
PACKAGE = EVALS.parent

NAME = "Fixture Author"
EMAIL = "fixture@example.invalid"
SUBJECT = "chore: record agent documentation audit"
CONTRACT_HEADING = "> ## Maintaining these files"

README_LABEL = (
    "This repository is a disposable evaluation fixture. Its history was\n"
    "constructed for testing agent-instruction tooling and does not record a\n"
    "real project's incidents.\n"
)
GITIGNORE = "__pycache__/\n.venv/\n"
CHECK_SH = """#!/bin/sh
# Run the unit tests from the repository root without writing bytecode caches.
set -eu
cd "$(dirname "$0")/.."
exec python3 -B -m unittest discover -s tests
"""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of the file at `path`"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def isolated_env(config_home: Path) -> dict[str, str]:
    """
    Return an environment that isolates Git from user and system settings

    User-wide templates, signing keys and ignore rules would make fixture SHAs
    machine-specific. Git reads `$XDG_CONFIG_HOME/git/ignore` even without a
    global config, and a user-wide ignore file can list AGENTS.md or
    CLAUDE.md, which would silently drop them from fixture commits. Pointing
    the variable at an empty directory prevents both.

    Parameters
    ----------
    config_home
        An empty directory to use as `XDG_CONFIG_HOME`.
    """
    env = dict(os.environ)
    env.update(
        XDG_CONFIG_HOME=str(config_home),
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME=NAME,
        GIT_AUTHOR_EMAIL=EMAIL,
        GIT_COMMITTER_NAME=NAME,
        GIT_COMMITTER_EMAIL=EMAIL,
        LC_ALL="C",
        TZ="UTC",
    )
    return env


def is_within(path: Path, directory: Path) -> bool:
    """Report whether `path` is `directory` or lies beneath it"""
    return path.resolve().is_relative_to(directory.resolve())


@dataclass(frozen=True)
class PinnedSkills:
    """
    The skill copies that executors receive and the fixtures quote

    Parameters
    ----------
    directory
        A directory holding `agents-md-audit/SKILL.md` and
        `agents-md-bootstrap/SKILL.md`.
    """

    directory: Path

    @property
    def audit(self) -> Path:
        """The pinned audit skill file"""
        return self.directory / "agents-md-audit/SKILL.md"

    @property
    def bootstrap(self) -> Path:
        """The pinned bootstrap skill file"""
        return self.directory / "agents-md-bootstrap/SKILL.md"

    @property
    def audit_revision(self) -> str:
        """The `Agents-Audit-Skill-Revision` value identifying the audit skill"""
        return f"sha256:{sha256_file(self.audit)}"

    def contract(self) -> str:
        """Return the maintenance contract quoted in the bootstrap skill"""
        lines = self.bootstrap.read_text(encoding="utf-8").splitlines()
        start = lines.index(CONTRACT_HEADING)
        block = []
        for line in lines[start:]:
            if not line.startswith(">"):
                break
            block.append(line[2:] if line.startswith("> ") else line[1:])
        return "\n".join(block) + "\n"


class Fixture:
    """
    A fixture repository under construction

    Parameters
    ----------
    path
        The repository directory, which must not exist yet.
    messages
        The directory receiving authored commit messages, kept outside the
        checkout so the worktree holds only fixture files.
    env
        The isolated Git environment.
    skills
        The pinned skills whose content the fixture quotes.
    """

    def __init__(
        self, path: Path, messages: Path, env: dict[str, str], skills: PinnedSkills
    ) -> None:
        if path.exists():
            sys.exit(f"refusing to replace existing fixture {path}")
        path.mkdir(parents=True)
        self.path = path
        self.messages = messages
        self.env = env
        self.skills = skills
        self.labels: dict[str, str] = {}
        self.git("init", "--quiet", "--template=", "--initial-branch=main")
        self.git("config", "user.name", NAME)
        self.git("config", "user.email", EMAIL)

    def git(self, *args: str, date: str | None = None, stdin: str | None = None) -> str:
        """Run Git in the fixture and return its stripped standard output"""
        env = dict(self.env)
        if date is not None:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            env=env,
            input=stdin,
            text=True,
            check=True,
            capture_output=True,
        ).stdout.strip()

    def write(self, rel: str, text: str, executable: bool = False) -> None:
        """Write `text` to the repository-relative path `rel`"""
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        target.chmod(0o755 if executable else 0o644)

    def commit(self, label: str, message: str, date: str) -> str:
        """Stage every change, commit it, and record its SHA under `label`"""
        self.git("add", "-A")
        self.git("commit", "--quiet", "--cleanup=verbatim", "-m", message, date=date)
        return self.remember(label)

    def remember(self, label: str) -> str:
        """Record the current HEAD under `label` and return it"""
        sha = self.git("rev-parse", "HEAD")
        self.labels[label] = sha
        return sha

    def message_file(self, label: str, text: str) -> Path:
        """Write a commit message outside the checkout and return its path"""
        self.messages.mkdir(parents=True, exist_ok=True)
        path = self.messages / f"{self.path.name}-{label}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def checkpoint(self, label: str, body: str, previous: str, date: str) -> str:
        """
        Create a checkpoint for HEAD with the audit skill's documented command

        Parameters
        ----------
        label
            The name under which the checkpoint SHA is recorded.
        body
            The report sections; the subject and trailers are added here so
            every checkpoint shares one template.
        previous
            The `Agents-Audit-Previous` value.
        date
            The author and committer date.

        Returns
        -------
        sha
            The checkpoint SHA, after confirming that it has one parent, an
            unchanged tree and the authored message byte for byte.
        """
        parent = self.git("rev-parse", "HEAD")
        tree = self.git("rev-parse", "HEAD^{tree}")
        text = checkpoint_text(body, parent, tree, previous, self.skills.audit_revision)
        path = self.message_file(label, text)
        self.git(
            "commit",
            "--quiet",
            "--allow-empty",
            "--only",
            "--cleanup=verbatim",
            "--file",
            str(path),
            date=date,
        )
        sha = self.remember(label)
        assert self.git("rev-parse", f"{sha}^{{tree}}") == tree
        assert self.git("show", "-s", "--format=%P", sha) == parent
        assert stored_message(self, sha) == text
        return sha

    def settle(self) -> None:
        """
        Leave an index that later read-only `git status` calls do not rewrite

        Files written in the same second as the index are racily clean, and Git
        rewrites the index when it next checks them. Waiting and refreshing once
        makes the raw index bytes a stable part of the before-state.
        """
        time.sleep(1.2)
        self.git("status", "--porcelain")
        first = sha256_file(self.path / ".git/index")
        self.git("status", "--porcelain")
        assert sha256_file(self.path / ".git/index") == first, self.path


def stored_message(fixture: Fixture, sha: str) -> str:
    """Return the raw message of commit `sha` as stored in the object"""
    raw = subprocess.run(
        ["git", "-C", str(fixture.path), "cat-file", "commit", sha],
        env=fixture.env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return raw.split("\n\n", 1)[1]


def checkpoint_text(
    body: str, commit: str, tree: str, previous: str, skill_revision: str
) -> str:
    """Return a complete checkpoint message following the audit skill template"""
    trailers = [
        "Agents-Audit-Version: 1",
        f"Agents-Audit-Commit: {commit}",
        f"Agents-Audit-Tree: {tree}",
        f"Agents-Audit-Skill-Revision: {skill_revision}",
        f"Agents-Audit-Previous: {previous}",
    ]
    return f"{SUBJECT}\n\n{body.strip()}\n\n" + "\n".join(trailers) + "\n"


def tool_versions() -> str:
    """Return the tool versions quoted in fixture coverage sections"""
    git = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, check=True
    )
    return f"{git.stdout.strip()} and Python 3 on macOS"


def run_tests(fx: Fixture) -> None:
    """Run the fixture's unit tests without writing bytecode into it"""
    subprocess.run(
        [
            "uv",
            "run",
            "--no-project",
            "python",
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-q",
        ],
        cwd=fx.path,
        check=True,
        capture_output=True,
        env=fx.env,
    )


# Tiny projects ------------------------------------------------------------

TALLY_PYPROJECT = """[project]
name = "tally"
version = "0.1.0"
description = "Count words in text files"
requires-python = ">=3.10"

[project.scripts]
tally = "tally.cli:main"
"""

TALLY_INIT = '''"""Count words in text."""

from tally.core import count_words

__all__ = ["count_words"]
'''

TALLY_CORE = '''"""Word-counting functions that operate on strings only."""


def count_words(text: str) -> dict[str, int]:
    """
    Count how often each whitespace-separated word occurs in `text`
    """
    counts: dict[str, int] = {}
    for word in text.split():
        counts[word] = counts.get(word, 0) + 1
    return counts
'''

TALLY_CORE_LOWER = '''"""Word-counting functions that operate on strings only."""


def count_words(text: str, lower: bool = False) -> dict[str, int]:
    """
    Count how often each whitespace-separated word occurs in `text`

    With `lower`, words that differ only in case count as one word.
    """
    if lower:
        text = text.lower()
    counts: dict[str, int] = {}
    for word in text.split():
        counts[word] = counts.get(word, 0) + 1
    return counts
'''

TALLY_CLI = '''"""Command-line interface that counts words in files."""

import argparse
import sys
from pathlib import Path

from tally.core import count_words


def main(argv: list[str] | None = None) -> int:
    """
    Print the count of each word in the named files
    """
    parser = argparse.ArgumentParser(prog="tally", description="Count words in text files.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    text = " ".join(path.read_text(encoding="utf-8") for path in args.paths)
    for word, count in sorted(count_words(text).items()):
        print(f"{count}\\t{word}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TALLY_CLI_LOWER = '''"""Command-line interface that counts words in files."""

import argparse
import sys
from pathlib import Path

from tally.core import count_words


def main(argv: list[str] | None = None) -> int:
    """
    Print the count of each word in the named files
    """
    parser = argparse.ArgumentParser(prog="tally", description="Count words in text files.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--lower", action="store_true", help="ignore letter case")
    args = parser.parse_args(argv)
    text = " ".join(path.read_text(encoding="utf-8") for path in args.paths)
    for word, count in sorted(count_words(text, lower=args.lower).items()):
        print(f"{count}\\t{word}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def tally_test(samples: str, lower: bool) -> str:
    """Return the tally test module reading inputs from `tests/<samples>`"""
    extra = (
        """
    def test_lower_merges_case(self) -> None:
        self.assertEqual(count_words("The the", lower=True), {"the": 2})
"""
        if lower
        else ""
    )
    return f'''import unittest
from pathlib import Path

from tally.core import count_words

SAMPLES = Path(__file__).parent / "{samples}"


class CountWordsTest(unittest.TestCase):
    def test_counts_repeated_words(self) -> None:
        self.assertEqual(count_words("a b a"), {{"a": 2, "b": 1}})

    def test_sample_file(self) -> None:
        text = (SAMPLES / "sample.txt").read_text(encoding="utf-8")
        self.assertEqual(count_words(text)["the"], 2)
{extra}

if __name__ == "__main__":
    unittest.main()
'''


def tally_readme(usage: bool = False) -> str:
    """Return the tally README, optionally with a usage section"""
    text = f"# tally\n\nCount words in text files.\n\n{README_LABEL}"
    if usage:
        text += "\n## Usage\n\n    tally --lower notes.txt\n"
    return text


def tally_agents(command: str, samples: str, core_path: str, contract: str = "") -> str:
    """Return a tally AGENTS.md with the given command and paths"""
    text = f"""# tally

Count words in text files.

## Commands

Run `{command}` from the repository root to run the unit tests. They need
Python 3.10 or later and no third-party packages.

## Layout

- `{core_path}` holds the counting functions.
- `tally/cli.py` implements the `tally` command declared in `pyproject.toml`.
- `tests/{samples}/` holds the text files that the tests read.
"""
    if contract:
        text += "\n" + contract
    return text


def write_tally(fx: Fixture, samples: str = "data", lower: bool = False) -> None:
    """Write the tally package, tests and helper files into `fx`"""
    fx.write("README.md", tally_readme())
    fx.write(".gitignore", GITIGNORE)
    fx.write("pyproject.toml", TALLY_PYPROJECT)
    fx.write("tally/__init__.py", TALLY_INIT)
    fx.write("tally/core.py", TALLY_CORE_LOWER if lower else TALLY_CORE)
    fx.write("tally/cli.py", TALLY_CLI_LOWER if lower else TALLY_CLI)
    fx.write(f"tests/{samples}/sample.txt", "the cat sat on the mat\n")
    fx.write("tests/test_core.py", tally_test(samples, lower))
    fx.write("scripts/check.sh", CHECK_SH, executable=True)


# Cases --------------------------------------------------------------------


def build_t1(fx: Fixture) -> None:
    """
    Build three-checkpoint history ending in ordinary commits

    C1 records `F1` and `F2`; C2 carries `F1`, closes `F2` and adds `F3`; later
    commits resolve `F3` and rename the test script named by AGENTS.md.
    """
    ids = {
        "F1": "AUD-20261001T090000Z-1",
        "F2": "AUD-20261001T090000Z-2",
        "F3": "AUD-20261008T090000Z-1",
    }
    write_tally(fx)
    fx.write("AGENTS.md", tally_agents("make test", "data", "tally/counter.py"))
    c0 = fx.commit(
        "c0",
        "feat: add word-count package (evaluation fixture)",
        "2026-09-30T09:00:00Z",
    )
    run_tests(fx)
    f1 = f"""{ids["F1"]}: AGENTS.md, "Layout", says that `tally/counter.py` holds the
counting functions. No such file exists; `git ls-files tally` lists
`tally/__init__.py`, `tally/cli.py` and `tally/core.py`, and `count_words` is
defined in `tally/core.py`. An agent following the instruction looks for a
missing module and may create a duplicate one. Replace `tally/counter.py` with
`tally/core.py`."""
    body1 = f"""## Coverage

Examined AGENTS.md, the only instruction file in the repository, and every
path and command it names.
Verified the layout claims against `git ls-files` and the sources, and checked
the test command against the repository; ran `sh scripts/check.sh`, which passed.
Inspected history from the root commit {c0} to the audited revision; this
audit establishes the initial history boundary.
Used {tool_versions()}.

## Unverified checks

Automatic delivery of AGENTS.md in the intended harness was not verified.

## New findings

{f1}

{ids["F2"]}: AGENTS.md, "Commands", says to run `make test`. The
repository has no Makefile or other make configuration; the unit tests run with
`sh scripts/check.sh`, which passed. An agent following the instruction gets a
failed command and no test result. Replace `make test` with
`sh scripts/check.sh`.

## Carried findings

None

## Closed findings

None
"""
    c1_cp = fx.checkpoint("C1", body1, "none", "2026-10-01T09:00:00Z")

    fx.write(
        "AGENTS.md", tally_agents("sh scripts/check.sh", "data", "tally/counter.py")
    )
    c1 = fx.commit(
        "c1", "docs: correct the test command in AGENTS.md", "2026-10-03T09:00:00Z"
    )
    fx.git("mv", "tests/data", "tests/samples")
    fx.write("tests/test_core.py", tally_test("samples", lower=False))
    c2 = fx.commit(
        "c2", "refactor: move test inputs to tests/samples", "2026-10-06T09:00:00Z"
    )
    run_tests(fx)
    body2 = f"""## Coverage

Examined AGENTS.md, the only instruction file in the repository, and every
path and command it names.
Verified the layout claims against `git ls-files` and the sources; ran
`sh scripts/check.sh`, which passed.
Inspected history from {c1_cp} to the audited revision.
Used {tool_versions()}.

## Unverified checks

Automatic delivery of AGENTS.md in the intended harness was not verified.

## New findings

{ids["F3"]}: AGENTS.md, "Layout", says that `tests/data/` holds the text
files that the tests read. Commit {c2} moved them to `tests/samples/`, and
`tests/test_core.py` now reads from `tests/samples/`; `tests/data/` no longer
exists. An agent adding a test input would put it where no test reads it.
Replace `tests/data/` with `tests/samples/`.

## Carried findings

{ids["F1"]} (source checkpoint {c1_cp}): AGENTS.md, "Layout", still says
that `tally/counter.py` holds the counting functions. No such file exists;
`git ls-files tally` lists `tally/__init__.py`, `tally/cli.py` and
`tally/core.py`, and `count_words` is defined in `tally/core.py`. An agent
following the instruction looks for a missing module and may create a duplicate
one. Replace `tally/counter.py` with `tally/core.py`.

## Closed findings

{ids["F2"]}: resolved in {c1}. AGENTS.md, "Commands", now says to run
`sh scripts/check.sh`; that script exists and ran the unit tests successfully.
"""
    fx.checkpoint("C2", body2, c1_cp, "2026-10-08T09:00:00Z")

    fx.write(
        "AGENTS.md", tally_agents("sh scripts/check.sh", "samples", "tally/counter.py")
    )
    fx.commit("c3", "docs: point AGENTS.md at tests/samples", "2026-10-12T09:00:00Z")
    fx.write("tally/core.py", TALLY_CORE_LOWER)
    fx.write("tally/cli.py", TALLY_CLI_LOWER)
    fx.write("tests/test_core.py", tally_test("samples", lower=True))
    fx.commit(
        "c4",
        "feat: add a --lower option that ignores letter case",
        "2026-10-15T09:00:00Z",
    )
    fx.git("mv", "scripts/check.sh", "scripts/run-tests.sh")
    fx.commit(
        "c5", "build: rename the test script to run-tests.sh", "2026-10-20T09:00:00Z"
    )
    run_tests(fx)


TEMPCONV_PYPROJECT = """[project]
name = "tempconv"
version = "0.1.0"
description = "Convert temperatures between units"
requires-python = ">=3.10"
"""

TEMPCONV_CONVERT = '''"""Temperature conversion functions."""


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from degrees Celsius to degrees Fahrenheit"""
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert a temperature from degrees Fahrenheit to degrees Celsius"""
    return (fahrenheit - 32) * 5 / 9
'''

TEMPCONV_KELVIN = (
    TEMPCONV_CONVERT
    + '''

def celsius_to_kelvin(celsius: float) -> float:
    """Convert a temperature from degrees Celsius to kelvins"""
    return celsius + 273.15
'''
)


def tempconv_test(kelvin: bool) -> str:
    """Return the tempconv test module"""
    names = (
        "celsius_to_fahrenheit, celsius_to_kelvin, fahrenheit_to_celsius"
        if kelvin
        else ("celsius_to_fahrenheit, fahrenheit_to_celsius")
    )
    extra = (
        """
    def test_kelvin(self) -> None:
        self.assertAlmostEqual(celsius_to_kelvin(0), 273.15)
"""
        if kelvin
        else ""
    )
    return f"""import unittest

from tempconv.convert import {names}


class ConvertTest(unittest.TestCase):
    def test_boiling_point(self) -> None:
        self.assertEqual(celsius_to_fahrenheit(100), 212)

    def test_round_trip(self) -> None:
        self.assertAlmostEqual(fahrenheit_to_celsius(celsius_to_fahrenheit(37)), 37)
{extra}

if __name__ == "__main__":
    unittest.main()
"""


TEMPCONV_AGENTS = """# tempconv

Convert temperatures between units.

## Commands

Run `sh scripts/check.sh` from the repository root to run the unit tests. They
need Python 3.10 or later and no third-party packages.

## Layout

- `tempconv/formulas.py` holds the conversion functions.
- `tests/test_convert.py` holds the unit tests.
"""


def build_t2(fx: Fixture) -> None:
    """
    Build a valid checkpoint followed by a replayed checkpoint-like commit

    `X` carries all five trailers, but its `Agents-Audit-Commit` names the
    pre-replay parent, which is pruned from the repository. `X` falsely closes
    the open finding and adds a finding about a tox command AGENTS.md lacks.
    """
    ids = {"F1": "AUD-20261002T100000Z-1", "BOGUS": "AUD-20261020T100000Z-1"}
    readme = f"# tempconv\n\nConvert temperatures between units.\n\n{README_LABEL}"
    fx.write("README.md", readme)
    fx.write(".gitignore", GITIGNORE)
    fx.write("pyproject.toml", TEMPCONV_PYPROJECT)
    fx.write("tempconv/__init__.py", '"""Convert temperatures between units."""\n')
    fx.write("tempconv/convert.py", TEMPCONV_CONVERT)
    fx.write("tests/test_convert.py", tempconv_test(kelvin=False))
    fx.write("scripts/check.sh", CHECK_SH, executable=True)
    fx.write("AGENTS.md", TEMPCONV_AGENTS)
    c0 = fx.commit(
        "c0",
        "feat: add temperature conversion package (evaluation fixture)",
        "2026-10-01T10:00:00Z",
    )
    run_tests(fx)
    body1 = f"""## Coverage

Examined AGENTS.md, the only instruction file in the repository, and every
path and command it names.
Verified the layout claims against `git ls-files` and the sources; ran
`sh scripts/check.sh`, which passed.
Inspected history from the root commit {c0} to the audited revision; this
audit establishes the initial history boundary.
Used {tool_versions()}.

## Unverified checks

Automatic delivery of AGENTS.md in the intended harness was not verified.

## New findings

{ids["F1"]}: AGENTS.md, "Layout", says that `tempconv/formulas.py` holds
the conversion functions. No such file exists; `git ls-files tempconv` lists
`tempconv/__init__.py` and `tempconv/convert.py`, and both conversion functions
are defined in `tempconv/convert.py`. An agent following the instruction looks
for a missing module and may add conversions in a new, untested file. Replace
`tempconv/formulas.py` with `tempconv/convert.py`.

## Carried findings

None

## Closed findings

None
"""
    c1_cp = fx.checkpoint("C1", body1, "none", "2026-10-02T10:00:00Z")

    fx.write("tempconv/convert.py", TEMPCONV_KELVIN)
    fx.write("tests/test_convert.py", tempconv_test(kelvin=True))
    fx.git("add", "-A")
    tree = fx.git("write-tree")
    message = "feat: add Celsius to kelvin conversion\n"
    author = "2026-10-10T10:00:00Z"
    original = commit_tree(fx, tree, c1_cp, message, author, "2026-10-10T10:00:00Z")
    replayed = commit_tree(fx, tree, c1_cp, message, author, "2026-10-18T10:00:00Z")
    fx.labels["d1_original_pruned"] = original
    fx.labels["d1"] = replayed
    body_x = f"""## Coverage

Examined AGENTS.md, the only instruction file in the repository, and every
path and command it names.
Verified the layout and command claims; ran `sh scripts/check.sh`, which
passed.
Inspected history from {c1_cp} to the audited revision.
Used {tool_versions()}.

## Unverified checks

Automatic delivery of AGENTS.md in the intended harness was not verified.

## New findings

{ids["BOGUS"]}: AGENTS.md, "Commands", tells agents to run `tox -e py312`
before committing, but the repository has no `tox.ini` or other tox
configuration. Following the instruction fails before any test runs. Remove the
tox instruction or add the configuration.

## Carried findings

None

## Closed findings

{ids["F1"]}: resolved in {original}. `tempconv/formulas.py` now holds the
conversion functions, as AGENTS.md states.
"""
    text = checkpoint_text(body_x, original, tree, c1_cp, fx.skills.audit_revision)
    path = fx.message_file("X", text)
    x = subprocess.run(
        [
            "git",
            "-C",
            str(fx.path),
            "commit-tree",
            tree,
            "-p",
            replayed,
            "-F",
            str(path),
        ],
        env={
            **fx.env,
            "GIT_AUTHOR_DATE": "2026-10-20T10:00:00Z",
            "GIT_COMMITTER_DATE": "2026-10-20T10:00:01Z",
        },
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    fx.git("update-ref", "refs/heads/main", x)
    fx.labels["X"] = x
    assert stored_message(fx, x) == text
    run_tests(fx)
    fx.write(
        "README.md",
        readme
        + "\n## Usage\n\n    >>> from tempconv.convert import celsius_to_fahrenheit\n"
        "    >>> celsius_to_fahrenheit(100)\n    212.0\n",
    )
    fx.commit("d2", "docs: add a usage example to the README", "2026-10-24T10:00:00Z")
    fx.git("reflog", "expire", "--expire=now", "--all")
    fx.git("gc", "--quiet", "--prune=now")
    missing = subprocess.run(
        ["git", "-C", str(fx.path), "cat-file", "-e", original],
        env=fx.env,
        capture_output=True,
        check=False,
    )
    assert missing.returncode != 0, "pre-replay commit still present"


def commit_tree(
    fx: Fixture, tree: str, parent: str, message: str, author: str, committer: str
) -> str:
    """Create a commit object for `tree` without moving any ref"""
    return subprocess.run(
        [
            "git",
            "-C",
            str(fx.path),
            "commit-tree",
            tree,
            "-p",
            parent,
            "-m",
            message.strip(),
        ],
        env={**fx.env, "GIT_AUTHOR_DATE": author, "GIT_COMMITTER_DATE": committer},
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def build_t3(fx: Fixture) -> None:
    """
    Build an accurate repository with uncommitted work and message cleanup

    The README change is staged, `scratch.txt` is untracked, and the local
    `commit.cleanup=strip` setting would remove `##` headings from a message
    committed without `--cleanup=verbatim`.
    """
    write_tally(fx, samples="samples")
    fx.write(
        "AGENTS.md",
        tally_agents(
            "sh scripts/check.sh", "samples", "tally/core.py", fx.skills.contract()
        ).replace(
            "- `tests/samples/` holds the text files that the tests read.\n",
            "- `tests/samples/` holds the text files that the tests read.\n\n"
            "## Rules\n\nKeep `tally/core.py` free of file and console I/O; "
            "`tally/cli.py` reads files and prints\nresults.\n",
        ),
    )
    fx.commit(
        "c0",
        "feat: add word-count package (evaluation fixture)",
        "2026-10-01T11:00:00Z",
    )
    fx.write("tally/core.py", TALLY_CORE_LOWER)
    fx.write("tally/cli.py", TALLY_CLI_LOWER)
    fx.write("tests/test_core.py", tally_test("samples", lower=True))
    fx.commit(
        "c1",
        "feat: add a --lower option that ignores letter case",
        "2026-10-05T11:00:00Z",
    )
    run_tests(fx)
    fx.write("README.md", tally_readme(usage=True))
    fx.git("add", "README.md")
    fx.write("scratch.txt", "Draft release notes, not ready to commit.\n")
    fx.git("config", "commit.cleanup", "strip")


SLUG_V0 = '''"""Convert titles to URL slugs."""

import re
import unicodedata


def slugify(title: str, separator: str = "-") -> str:
    """
    Convert `title` to a lowercase ASCII slug joined by `separator`
    """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", separator, ascii_title.lower().strip())
'''

SLUG_V1 = '''"""Convert titles to URL slugs."""

import re
import unicodedata


def slugify(title: str, separator: str = "-") -> str:
    """
    Convert `title` to a lowercase ASCII slug joined by `separator`

    Each run of characters other than ASCII letters and digits becomes one
    separator, and the slug never starts or ends with a separator.
    """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    return separator.join(re.findall(r"[a-z0-9]+", ascii_title.lower()))
'''


def slug_test(collapse: bool) -> str:
    """Return the slugkit test module"""
    extra = (
        """
    def test_collapses_repeated_separators(self) -> None:
        self.assertEqual(slugify("  Hello -- World!  "), "hello-world")
"""
        if collapse
        else ""
    )
    return f"""import unittest

from slugkit import slugify


class SlugifyTest(unittest.TestCase):
    def test_lowercases_words(self) -> None:
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_strips_accents(self) -> None:
        self.assertEqual(slugify("Café"), "cafe")
{extra}

if __name__ == "__main__":
    unittest.main()
"""


SLUG_CLAUDE = """# slugkit

Turn titles into URL slugs.

Run the tests with `python3 -B -m unittest discover -s tests` from the
repository root.

## Release policy

Add an entry under `## Unreleased` in `CHANGELOG.md` for every user-visible
change, in the same commit as the change.
"""


def build_t4(fx: Fixture) -> None:
    """
    Build a repository whose CLAUDE.md states an unenforced release policy

    A rationale for the separator fix appears only in a commit message, so
    bootstrap output that repeats it has mined history.
    """
    fx.write("README.md", f"# slugkit\n\nTurn titles into URL slugs.\n\n{README_LABEL}")
    fx.write(".gitignore", GITIGNORE)
    fx.write(
        "pyproject.toml",
        '[project]\nname = "slugkit"\nversion = "0.1.0"\n'
        'description = "Turn titles into URL slugs"\nrequires-python = ">=3.10"\n',
    )
    fx.write(
        "slugkit/__init__.py",
        '"""Turn titles into URL slugs."""\n\nfrom slugkit.slug import slugify\n\n__all__ = ["slugify"]\n',
    )
    fx.write("slugkit/slug.py", SLUG_V0)
    fx.write("tests/test_slug.py", slug_test(collapse=False))
    fx.write(
        "CHANGELOG.md", "# Changelog\n\n## Unreleased\n\n## 0.1.0\n\n- Add `slugify`.\n"
    )
    fx.write("CLAUDE.md", SLUG_CLAUDE)
    fx.commit("c0", "feat: add slugify (evaluation fixture)", "2026-10-01T12:00:00Z")
    fx.write("slugkit/slug.py", SLUG_V1)
    fx.write("tests/test_slug.py", slug_test(collapse=True))
    fx.write(
        "CHANGELOG.md",
        "# Changelog\n\n## Unreleased\n\n- Collapse repeated separators in slugs.\n\n## 0.1.0\n\n- Add `slugify`.\n",
    )
    fx.commit(
        "c1",
        "fix: collapse repeated separators\n\n"
        "The legacy Apache rewrite rules on the documentation server reject\n"
        "slugs that contain double hyphens, so each run of separators must\n"
        "become one.",
        "2026-10-04T12:00:00Z",
    )
    run_tests(fx)


# Snapshot -----------------------------------------------------------------


def snapshot(repo: Path, env: dict[str, str]) -> JsonObject:
    """
    Capture the repository state that a read-only run must preserve

    Inspection runs with `GIT_OPTIONAL_LOCKS=0` so capturing the state does
    not refresh the index it records.
    """
    env = {**env, "GIT_OPTIONAL_LOCKS": "0"}

    def git(*args: str) -> str:
        """Run a read-only Git command in `repo` and return its output"""
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

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
        "head": git("rev-parse", "HEAD").strip(),
        "head_tree": git("rev-parse", "HEAD^{tree}").strip(),
        "head_ref": git("symbolic-ref", "-q", "HEAD").strip(),
        "status_porcelain_v2": git("status", "--porcelain=v2", "--untracked-files=all"),
        "status_ignored": git(
            "status", "--porcelain=v2", "--ignored", "--untracked-files=all"
        ),
        "index_sha1": hashlib.sha1(index).hexdigest(),
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "ls_files_stage": git("ls-files", "-s"),
        "staged_diff_sha256": hashlib.sha256(
            git("diff", "--cached", "--binary").encode()
        ).hexdigest(),
        "refs": git("for-each-ref", "--format=%(objectname) %(refname)"),
        "local_config": git("config", "--local", "--list"),
        "commit_count": git("rev-list", "--count", "--all").strip(),
        "files": files,
    }


def executor_ignored_names(repo: Path) -> list[str]:
    """
    Return instruction paths that the user's own Git ignore rules match

    Executors run with the user's Git configuration rather than the isolated
    build environment. Instruction files they create under a matching rule
    appear as ignored rather than untracked, which affects how their output
    must be inspected.
    """
    names = ["AGENTS.md", "CLAUDE.md", ".agents/", ".claude/"]
    result = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "--no-index", *names],
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.split()


def version(*command: str) -> str:
    """Return the first line a version command prints, or why it failed"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        return f"unavailable: {error}"
    return result.stdout.strip()


# Main ---------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse and validate the trial root, skills and run directory arguments"""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--trial-root",
        type=Path,
        required=True,
        help="directory for fixtures, executor outputs and the empty Git config",
    )
    parser.add_argument(
        "--skills",
        type=Path,
        required=True,
        help="pinned copy of the package's skills directory",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="directory for the run manifest, bundles, messages and assessments",
    )
    args = parser.parse_args()
    for name in ("trial_root", "skills", "run_dir"):
        setattr(args, name, getattr(args, name).absolute())
    if is_within(args.trial_root, PACKAGE):
        parser.error("--trial-root must lie outside the package")
    if is_within(args.skills, PACKAGE):
        parser.error("--skills must be a pinned copy outside the package")
    if any(is_within(args.run_dir, PACKAGE / part) for part in ("evals", "skills")):
        parser.error("--run-dir must lie outside the package's evals and skills")
    return args


def main() -> None:
    """Build the fixtures and write the run manifest"""
    args = parse_args()
    skills = PinnedSkills(args.skills)
    for path in (skills.audit, skills.bootstrap):
        if not path.is_file():
            sys.exit(f"missing pinned skill {path}")
    config_home = args.trial_root / "builder-xdg-empty"
    config_home.mkdir(parents=True, exist_ok=True)
    env = isolated_env(config_home)
    fixtures = args.trial_root / "fixtures"
    outputs = args.trial_root / "outputs"
    messages = args.run_dir / "messages"

    builders = {"T1": build_t1, "T2": build_t2, "T3": build_t3, "T4": build_t4}
    built: dict[str, Fixture] = {}
    for case, build in builders.items():
        fx = Fixture(fixtures / case, messages, env, skills)
        build(fx)
        fx.settle()
        fx.remember("HEAD")
        built[case] = fx

    source = subprocess.run(
        ["git", "-C", str(PACKAGE), "rev-parse", "HEAD", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    requests = json.loads((EVALS / "requests.json").read_text(encoding="utf-8"))
    skill_files = {
        "agents-md-audit": skills.audit,
        "agents-md-bootstrap": skills.bootstrap,
    }

    def request(case: str) -> str:
        """Return the executor request for `case` with its paths filled in"""
        template = requests[case]
        return str(template["text"]).format(
            skill=skill_files[template["skill"]], out=outputs / case
        )

    bundles = args.run_dir / "bundles"
    bundles.mkdir(parents=True, exist_ok=True)
    manifest: JsonObject = {
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "label": "Evaluation fixtures with introduced conditions; no real project incidents.",
        "trial_root": str(args.trial_root),
        "source": {"repository": str(PACKAGE), "head": source[0], "tree": source[1]},
        "skills": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in skill_files.items()
        },
        "environment": {
            "git": version("git", "--version"),
            "python": platform.python_version(),
            "uv": version("uv", "--version"),
            "platform": platform.platform(),
            "fixture_git_isolation": (
                "Built with GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1, an empty "
                "XDG_CONFIG_HOME and an empty template."
            ),
            "executor_ignored_instruction_paths": executor_ignored_names(
                built["T1"].path
            ),
        },
        "ignored_instruction_files": "None in any fixture.",
        "cases": {},
    }
    for case, fx in built.items():
        bundle = bundles / f"{case}.bundle"
        subprocess.run(
            [
                "git",
                "-C",
                str(fx.path),
                "bundle",
                "create",
                "--quiet",
                str(bundle),
                "--all",
            ],
            env={**env, "GIT_OPTIONAL_LOCKS": "0"},
            check=True,
            capture_output=True,
        )
        (outputs / case).mkdir(parents=True, exist_ok=True)
        manifest["cases"][case] = {
            "fixture": str(fx.path),
            "workdir": str(fx.path),
            "output_dir": str(outputs / case),
            "request": request(case),
            "commits": fx.labels,
            "bundle": str(bundle),
            "bundle_sha256": sha256_file(bundle),
            "before": snapshot(fx.path, env),
        }
    (outputs / "T5").mkdir(parents=True, exist_ok=True)
    manifest["cases"]["T5"] = {
        "fixture": str(fixtures / "T5"),
        "workdir": str(fixtures / "T5"),
        "output_dir": str(outputs / "T5"),
        "request": request("T5"),
        "pending": (
            "Created after the T4 run by build_repeat_fixture.py; its before-state "
            "is in manifest-T5.json."
        ),
    }
    (args.run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({case: fx.labels for case, fx in built.items()}, indent=2))


if __name__ == "__main__":
    main()
