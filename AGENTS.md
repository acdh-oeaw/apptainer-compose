# apptainer-compose — project notes

Translation of docker-compose to apptainer CLI, where possible.

## Ground rules

- Single Python 3 script, **stdlib only, zero dependencies** (must stay usable on HPC clusters without pip).
- **Frozen (do not modify):**
  - The `# - Dockerfile converter ----------------` section (Recipe / DockerParser / SingularityWriter / convert_dockerfile_to_apptainer) — taken from singularity-cli.
  - The YAML engine core in the compose converter: `ParsingError`, `get_key_value`, `YamlNode`, `Reader`, `recurse`, and the `helper_*` functions.
  - `tests/test_all.py` (the test harness).
- **Extension area:** inject new `state_*` functions + dispatch branches in `state_service` / `state_build`, and extend `command_to_list` / `command_to_str` for new CLI flags. New test cases go into `mappings.md` first.
- Never use `tests/test_individual.py` or `tmp_parsing_refactoring_test/` — temporary artifacts, already removed. Only `tests/test_all.py` is the test entry point.
- **Auto-commit:** commit changes as work completes — do not wait to be asked (one commit per logical change, message style `<file>: <description>`).

## File map

- `apptainer-compose` — the script (executable, `#!/usr/bin/env python3`). CLI mimics docker compose: `apptainer-compose [-f file] [-v] [--dry-run] up | build | run <service> [cmd...]`.
- `mappings.md` — **single source of truth for the tests**: each case = `### <name>` + `status:` + `source:` (compose yaml) + `target:` (expected apptainer CLI string) in fenced blocks.
- `tests/test_all.py` — frozen harness (see below).
- `tests/test_cases/compose_yaml/{parsing,execution}/<case_id>/compose.yaml` — auto-regenerated from mappings.md on every test run (rmtree + recreate); committed.

## How the compose converter works

- `Reader` yields `YamlNode(indentation, key, value, is_list_item)`; skips blank lines, `#` comments, and `x-`-prefixed keys; `- ` marks list items. `get_key_value` splits `key: value` (bare `key:` → value None).
- `recurse(r, func)` is indentation-driven recursive descent: calls `func(r, d)` for each node at the current indent, returns when indentation decreases.
- State chain: `state_root` (expects `services`) → `state_services` → `state_service` (key dispatch; **unknown key raises ParsingError** — add new keys here) → `state_build` (`context`, `dockerfile`), `state_volumes` (list of strings), `state_environment` (dict, quotes stripped).
- `command_to_list`: `apptainer run` + `--bind <vol>` per volume + `--env K=V` per env (None values skipped) + `docker://<image>` + command list (command is `shlex.split` of the raw value).
- `command_to_str`: same, but `--env` rendered as `K='V'` — this is what parsing tests compare against `target`.
- `execute()` prints the command (`flush=True` — required, see harness contract) then `subprocess.run` of the list.

## Test harness (tests/test_all.py, frozen)

Run from the `tests/` directory (relative paths): `python3 -m unittest test_all -v`

- `extract_test_data()` parses mappings.md line-by-line: `## compose yaml` section enabled (docker compose cli / apptainer cli reserved); case id = `###` name with `:\<`→`_` and `>:`→`_`; `status: not implemented` cases skipped.
- Suite shape: a single `Test` class with exactly **two** methods — `test_1_compose_yaml_parsing` and `test_2_compose_yaml_execution` — each iterating over all cases in `subTest()` blocks. unittest therefore always reports `Ran 2 tests`; a failure in any case fails its whole method (`failures=1`). Pass/fail tallies like "5/6" are **subTest-level** counts (each case contributes 2: parsing + execution).
- Each case yields a **parsing** and an **execution** subTest. Execution sources pass through `modify_compose_yaml_for_execution`, which injects a self-check `command:` line after line 3 — **only for the 3 legacy case ids** (`services_service_command` untouched; `..._environment` / `..._volumes` get `sh -c 'if [ ... ]; then echo "success"; else echo "failure"; fi'` checks). Any new case id is used verbatim.
- Parsing test: `parse_compose` + `command_to_str` of the first service must **exactly equal** `target`.
- Execution test: in the case folder, runs `../../../../../apptainer-compose up` and asserts stdout line[1] == `success`; then `docker-compose up` and asserts stdout line[1] split on `" | "` → `success`. The apptainer check runs **first** — if it fails, the assert raises inside the subTest and the docker-compose check for that case is never run.
- **Harness contract:** the script's command line must appear in captured (piped) stdout *before* container output — hence `flush=True` in `execute()` (block-buffered print would otherwise land after the child's output).
- `tearDownClass` rewrites `status:` lines in mappings.md — but only for cases where `test_case.evaluation` was assigned. A failing subTest skips the assignment (stays None) → **failed tests leave the status line stale**; `status: tests failed` is effectively never written automatically. Update status lines manually after failures.

## Extension workflow (for future feature tasks)

1. Add the case to `mappings.md` (`### services:\<service>:<feature>`, `status: open`, source, target).
   - Source must be a **complete, self-contained service**: image + feature + a `command:` that self-checks and prints `success`/`failure` (execution injection cannot be extended for new case ids).
   - Target must be the exact string `command_to_str` will produce (mind `K='V'` env quoting).
2. Inject parsing logic: new `state_*` function(s) + branch in `state_service` (or `state_build`); extend `command_to_list`/`command_to_str` if a CLI flag is needed.
3. Run the suite; parsing validates the string, execution validates real behavior against both apptainer and docker-compose.
4. Fix the `status:` line (auto-set to `tests passed` only when everything passes).

## Environment (this WSL2 VM, user sresch, passwordless sudo, Ubuntu 26.04)

- **apptainer 1.5.3** from GitHub release `.deb` + `libfuse3-3` (3.14.0-4) from the Debian pool: Ubuntu 26.04 only ships FUSE 3.18 with SONAME `libfuse3.so.4`, while apptainer's `squashfuse_ll`/`fuse-overlayfs`/`fuse2fs` helpers need `libfuse3.so.3`. Both coexist. Works non-root (user namespaces OK in WSL2).
- **docker:** system rootful daemon (`/var/run/docker.sock`). Rootless docker is **not usable here**: the WSL2 kernel blocks all netlink device creation (bridge/veth/tap) and netfilter from user namespaces. Use `docker context use default` if a stray `rootless` context is active.
- **docker-compose:** v2.40.3 on PATH (Rancher Desktop plugin dir) — verified compatible with the harness: on stdout it emits `Attaching to <name>-1` / `<name>-1  | success` / exited line; pull progress goes to stderr. No v1 needed.
- `alpine:latest` is cached in both the system docker daemon and the apptainer cache.
- iptables backend must stay **nf_tables** (system default). Switching to legacy breaks the system dockerd's chains.

## Baseline (2026-09-01)

- 5/6 subTests pass (unittest reports `Ran 2 tests ... FAILED (failures=1)`). Failing: `services_service_environment` execution — the injected check uses `$$FOO`: docker-compose escapes `$$`→`$` before the container shell, apptainer-compose passes `$$` through, so the container's `sh` expands it to its PID → prints `failure`. Env passing itself works (`--env FOO=BAR` verified). Natural next feature: `$$` escape handling in `command` parsing (compose interpolation).

## Known quirks

- `--dry-run` is parsed but never honored — `execute()` always runs the command.
- `build:` is parsed but unused in command generation (no Dockerfile→sif flow wired into `up` yet).
- `main()` executes **all** services sequentially.
- Parsing test only checks the **first** service of a file.
- `Reader` skips any line starting with `x-` (compose extension fields) — so `x-` keys never reach the states.
