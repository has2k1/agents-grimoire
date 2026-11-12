"""
Build the T5 repeat-bootstrap fixture from the worktree that a T4 run left

T5 is a fresh clone of the pristine T4 bundle with every file of the T4
worktree copied over and committed with a fixed identity and date, so T5
starts from T4's output as committed work. Caches are not copied. Instruction
files are committed even when the user's Git ignore rules list AGENTS.md or
CLAUDE.md, because the build environment reads an empty configuration
directory instead.

Run after assessing T4, with the run directory that `build_fixtures.py`
wrote::

    python3 -I evals/build_repeat_fixture.py --run-dir /tmp/grimoire-evals-run

The fixture goes to the T5 location in the run manifest, the before-state to
`manifest-T5.json` and the bundle to `bundles/T5.bundle` in the run directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, TypeAlias

# A decoded JSON object, such as the run manifest or an expected outcome.
JsonObject: TypeAlias = dict[str, Any]

NAME = "Fixture Author"
EMAIL = "fixture@example.invalid"
DATE = "2026-11-12T12:00:00Z"
CACHE_PARTS = {"__pycache__", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of the file at `path`"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def isolated_env(config_home: Path) -> dict[str, str]:
    """
    Return the isolated Git environment used to build fixtures

    Parameters
    ----------
    config_home
        An empty directory to use as `XDG_CONFIG_HOME`, so user-wide ignore
        rules cannot drop instruction files from the harness commit.
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
        GIT_AUTHOR_DATE=DATE,
        GIT_COMMITTER_DATE=DATE,
        LC_ALL="C",
        TZ="UTC",
    )
    return env


def git(
    repo: Path, env: dict[str, str], *args: str, optional_locks: bool = True
) -> str:
    """Run Git in `repo` and return its standard output"""
    if not optional_locks:
        env = {**env, "GIT_OPTIONAL_LOCKS": "0"}
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def worktree_files(repo: Path) -> list[str]:
    """Return repository-relative files outside `.git` and caches"""
    files = []
    for path in sorted(repo.rglob("*")):
        rel = path.relative_to(repo)
        if (
            rel.parts[0] == ".git"
            or CACHE_PARTS & set(rel.parts)
            or path.is_dir()
            or rel.suffix == ".pyc"
        ):
            continue
        files.append(str(rel))
    return files


def snapshot(repo: Path, env: dict[str, str]) -> JsonObject:
    """Capture the before-state in the same form as `build_fixtures.py`"""
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

    def run(*args: str) -> str:
        """Run a read-only Git command in `repo` and return its output"""
        return git(repo, env, *args, optional_locks=False)

    return {
        "head": run("rev-parse", "HEAD").strip(),
        "head_tree": run("rev-parse", "HEAD^{tree}").strip(),
        "head_ref": run("symbolic-ref", "-q", "HEAD").strip(),
        "status_porcelain_v2": run("status", "--porcelain=v2", "--untracked-files=all"),
        "status_ignored": run(
            "status", "--porcelain=v2", "--ignored", "--untracked-files=all"
        ),
        "index_sha1": hashlib.sha1(index).hexdigest(),
        "index_sha256": hashlib.sha256(index).hexdigest(),
        "ls_files_stage": run("ls-files", "-s"),
        "staged_diff_sha256": hashlib.sha256(
            run("diff", "--cached", "--binary").encode()
        ).hexdigest(),
        "refs": run("for-each-ref", "--format=%(objectname) %(refname)"),
        "local_config": run("config", "--local", "--list"),
        "commit_count": run("rev-list", "--count", "--all").strip(),
        "files": files,
    }


def parse_args() -> argparse.Namespace:
    """Parse the run directory and the optional T4 worktree override"""
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="run directory holding the manifest that build_fixtures.py wrote",
    )
    parser.add_argument(
        "--t4-worktree",
        type=Path,
        help="T4 worktree to copy (default: the T4 fixture in the run manifest)",
    )
    return parser.parse_args()


def main() -> None:
    """Build T5 and write its before-state record"""
    args = parse_args()
    run_dir = args.run_dir.absolute()
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    t4 = manifest["cases"]["T4"]
    t5 = manifest["cases"]["T5"]
    source = (args.t4_worktree or Path(t4["fixture"])).absolute()
    target = Path(t5["fixture"])
    config_home = Path(manifest["trial_root"]) / "builder-xdg-empty"
    config_home.mkdir(parents=True, exist_ok=True)
    env = isolated_env(config_home)
    if target.exists():
        sys.exit(f"refusing to replace existing fixture {target}")
    head = git(source, env, "rev-parse", "HEAD", optional_locks=False).strip()
    if head != t4["before"]["head"]:
        sys.exit(
            f"T4 HEAD moved from {t4['before']['head']} to {head}; "
            "review the T4 run before building T5"
        )

    subprocess.run(
        ["git", "clone", "--quiet", "--template=", t4["bundle"], str(target)],
        env=env,
        check=True,
        capture_output=True,
    )
    git(target, env, "remote", "remove", "origin")
    git(target, env, "config", "user.name", NAME)
    git(target, env, "config", "user.email", EMAIL)

    copied = worktree_files(source)
    for rel in copied:
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, dest)
        dest.chmod((source / rel).stat().st_mode & 0o777)
    removed = [
        rel for rel in git(target, env, "ls-files").splitlines() if rel not in copied
    ]
    for rel in removed:
        (target / rel).unlink()

    git(target, env, "add", "-A")
    changed = git(target, env, "diff", "--cached", "--name-status")
    if changed:
        git(
            target,
            env,
            "commit",
            "--quiet",
            "--cleanup=verbatim",
            "-m",
            "docs: commit agents-md-bootstrap output (evaluation harness)",
        )
    # Files written in the same second as the index are racily clean; waiting
    # and refreshing once keeps later read-only `git status` calls from
    # rewriting the index bytes recorded below.
    time.sleep(1.2)
    git(target, env, "status", "--porcelain")
    first = sha256_file(target / ".git/index")
    git(target, env, "status", "--porcelain")
    assert sha256_file(target / ".git/index") == first

    bundle = run_dir / "bundles/T5.bundle"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(target), "bundle", "create", "--quiet", str(bundle), "--all"],
        env={**env, "GIT_OPTIONAL_LOCKS": "0"},
        check=True,
        capture_output=True,
    )
    Path(t5["output_dir"]).mkdir(parents=True, exist_ok=True)
    harness_commit = (
        git(target, env, "rev-parse", "HEAD", optional_locks=False).strip()
        if changed
        else None
    )
    record = {
        "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fixture": str(target),
        "source_t4_worktree": str(source),
        "t4_head": head,
        "harness_commit": harness_commit,
        "t4_changes": changed,
        "removed_from_t4_base": removed,
        "request": t5["request"],
        "output_dir": t5["output_dir"],
        "bundle": str(bundle),
        "bundle_sha256": sha256_file(bundle),
        "before": snapshot(target, env),
    }
    (run_dir / "manifest-T5.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {k: record[k] for k in ("fixture", "harness_commit", "t4_changes")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
