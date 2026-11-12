.PHONY: check dev

# Deterministic checks: whitespace, harness lint and types, skill discovery in
# the package files alone, and a fixture build with its self-test. Discovery
# runs on a copy of the tracked and unignored files, so a `make dev` link
# cannot hide a packaging error.
check:
	git diff --check
	uvx ruff check evals
	uvx ruff format --check evals
	uvx mypy --strict --python-version 3.12 --cache-dir "$${TMPDIR:-/tmp}/grimoire-mypy" evals
	@tmp=$${TMPDIR:-/tmp} && root=$$(mktemp -d "$${tmp%/}/grimoire-check.XXXXXX") && \
	mkdir "$$root/package" && \
	git ls-files -co --exclude-standard -z | tar --null -T - -cf - | tar -xf - -C "$$root/package" && \
	npx --yes skills add "$$root/package" --list && \
	cp -R skills "$$root/skills" && \
	python3 -I evals/build_fixtures.py --trial-root "$$root" \
		--skills "$$root/skills" --run-dir "$$root/run" > /dev/null && \
	python3 -I evals/assess.py --run-dir "$$root/run" selftest > /dev/null && \
	echo "Fixture build and self-test passed in $$root"

# Link the maintainer skills where harnesses discover them by name:
# `.agents/skills/` for Codex and `.claude/skills/` for Claude Code.
dev:
	@for dir in .agents/skills .claude/skills; do \
		mkdir -p "$$dir" && \
		if [ -e "$$dir/run-trials" ] && [ ! -L "$$dir/run-trials" ]; then \
			echo "$$dir/run-trials exists and is not a link; leaving it" >&2; exit 1; \
		fi && \
		ln -sfn ../../evals/run-trials "$$dir/run-trials" && \
		echo "Linked $$dir/run-trials"; \
	done
