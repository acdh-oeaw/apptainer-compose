# apptainer-compose — project notes

Translation of docker-compose to apptainer CLI, where possible.

## Ground rules

- Single Python 3 script, **stdlib only, zero dependencies** (must stay usable on HPC clusters without pip).
- **Frozen (do not modify):**
  - The `# - Dockerfile converter ----------------` section (Recipe / DockerParser / SingularityWriter / convert_dockerfile_to_apptainer) — taken from singularity-cli.
  - The YAML engine core in the compose converter: `ParsingError`, `get_key_value`, `YamlNode`, `Reader`, `recurse`, and the `helper_*` functions.
  - `tests/test_all.py` (the test harness).
- **Extension area:** inject new `state_*` functions + dispatch branches in `state_service` / `state_build`, and extend `command_to_list` / `command_to_str` for new CLI flags. For docker compose cli mappings, additionally adapt `parse_args()` (new flags/subcommands) and `execute()` as needed. New test cases go into `mappings.md` first.
- Never use `tests/test_individual.py` or `tmp_parsing_refactoring_test/` — temporary artifacts, already removed. Only `tests/test_all.py` is the test entry point.
- **Auto-commit & push:** commit changes as work completes and push to `origin` — do not wait to be asked (one commit per logical change, message style `<file>: <description>`).
- **Never truncate test output:** run the suite without `head`/`tail`/`grep`-style filtering — read the full output to judge results.
- **Test selection:** while developing a new feature, run only the appropriate test batch (e.g. docker compose cli → `python3 -m unittest test_all.Test.test_3_compose_cli_execution -v`). But after the feature is done and its tests pass, run the **full suite** (`python3 -m unittest test_all -v`) before committing, to guarantee no regressions slip in.
- **Security is secondary:** apptainer does not aim for full isolation like docker — everything regarding security (caps, privileged, seccomp, IPC/UTS namespace control) is secondary. Do not invest in mapping it: `security_opt` supports only `no-new-privileges` (other values raise ParsingError by design), cap_add/cap_drop/privileged/ipc are blacklisted.

## File map

- `apptainer-compose` — the script (executable, `#!/usr/bin/env python3`). CLI mimics docker compose: `apptainer-compose [-f file] [-v] [--dry-run] up | build | run <service> [cmd...]`.
- `mappings.md` — **single source of truth for the tests**, three sections: `## compose yaml` (`source:` = compose yaml, `target:` = expected apptainer CLI string; parsing + execution), `## docker compose cli` (`source:` = docker compose CLI command, `target:` = equivalent `apptainer-compose` command; execution only), `## apptainer cli` (reserved, currently not present). Each case = `### <name>` + `status:` + `source:`/`target:` in fenced blocks. Status semantics: `open` = **current focus** (work on it next); `not implemented` = **do not implement** (out of scope, leave as-is — e.g. `networks`).
- `tests/test_all.py` — frozen harness (see below).
- `tests/test_cases/compose_yaml/{parsing,execution}/<case_id>/compose.yaml` and `tests/test_cases/docker_compose_cli/execution/<case_id>/<fixture file>` (default `compose.yaml`; the `_f` case gets the file name from its `-f` argument) — auto-regenerated from mappings.md on every test run (rmtree + recreate); committed.

## How the compose converter works

- `Reader` yields `YamlNode(indentation, key, value, is_list_item)`; skips blank lines, `#` comments, and `x-`-prefixed keys; `- ` marks list items. `get_key_value` splits `key: value` (bare `key:` → value None).
- `recurse(r, func)` is indentation-driven recursive descent: calls `func(r, d)` for each node at the current indent, returns when indentation decreases.
- State chain: `state_root` (expects `services`; top-level `version` is accepted and ignored — consumed so the frozen `recurse` loop keeps advancing) → `state_services` → `state_service` (key dispatch; **unknown key raises ParsingError** — add new keys here) → `state_build` (`context`, `dockerfile`), `state_volumes` / `state_dns` / `state_security_opt` (list of strings), `state_environment` (dict **or** list of `KEY=VALUE`, quotes stripped — list items are detected by `key is None`, **not** `is_list_item`: the frozen Reader's `is_list_item` flag is sticky, set permanently once any `- ` line was seen), `state_labels` (dict, stored but **ignored** — no CLI flag), `state_profiles` (list of strings, honored on `up`); scalar keys (`image`, `hostname`, `working_dir`, `read_only`, `init`) stored directly; `command` / `entrypoint` are `shlex.split` of the raw value after compose `$$`→`$` interpolation.
- `command_to_list`: `apptainer run` (or `apptainer exec` if the service sets `entrypoint`; same for the `run` subcommand) + `--bind <vol>` per volume + `--env K=V` per env (dict or list form, None values skipped) + `--hostname H` + `--cwd D` (working_dir) + `--dns a,b` (comma-joined) + `--security no_new_privs` (per `security_opt: no-new-privileges`) + `--writable-tmpfs` (per `read_only: false` — apptainer's rootfs is read-only by default, docker's is writable) + `--no-init` (per `init: false`; apptainer runs its internal signal-capturing process by default) + `docker://<image>` + entrypoint list (if set) + command list.
- `command_to_str`: same, but `--env` rendered as `K='V'` — this is what parsing tests compare against `target`.
- `execute()` prints the command (`flush=True` — required, see harness contract), then `subprocess.run` of the list unless `--dry-run` (prints only); a non-zero child exit code is propagated via `sys.exit`.

## Test harness (tests/test_all.py, frozen)

Run from the `tests/` directory (relative paths). Either the full suite:

```
python3 -m unittest test_all -v
```

or individual test batches (one per suite method):

```
python3 -m unittest test_all.Test.test_1_compose_yaml_parsing -v
python3 -m unittest test_all.Test.test_2_compose_yaml_execution -v
python3 -m unittest test_all.Test.test_3_compose_cli_execution -v
```

- `extract_test_data()` parses mappings.md line-by-line: `## compose yaml` and `## docker compose cli` sections enabled (`## apptainer cli` reserved — recognized, but `create_test_case_data` returns early, so no cases are generated); case id = `###` name with `:\<`→`_`, `>:`→`_`, and `-`→`_` (so `-f` → `_f`); `status: not implemented` cases skipped.
- Suite shape: a single `Test` class with exactly **three** methods — `test_1_compose_yaml_parsing`, `test_2_compose_yaml_execution`, and `test_3_compose_cli_execution` — each iterating over its cases in `subTest()` blocks. unittest therefore always reports `Ran 3 tests`; a failure in any case fails its whole method (`failures=1`). Pass/fail tallies like "5/6" are **subTest-level** counts (each compose yaml case contributes 2: parsing + execution; each docker compose cli case contributes 1: execution).
- Compose yaml cases yield a **parsing** and an **execution** subTest. Execution sources pass through `modify_compose_yaml_for_execution`, which injects a self-check `command:` line after line 3 — **only for the 3 legacy case ids** (`services_service_command` untouched; `..._environment` / `..._volumes` get `sh -c 'if [ ... ]; then echo "success"; else echo "failure"; fi'` checks). Any new case id is used verbatim.
- Parsing test: `parse_compose` + `command_to_str` of the first service must **exactly equal** `target`.
- Execution test (compose yaml): in the case folder, runs `../../../../../apptainer-compose up` and asserts stdout line[1] == `success`; then `docker-compose up` and asserts stdout line[1] split on `" | "` → `success`. The apptainer check runs **first** — if it fails, the assert raises inside the subTest and the docker-compose check for that case is never run.
- Docker compose cli cases (execution only): `create_test_case_data` strips the trailing newline from `source` and rewrites `docker compose` → `docker-compose` (the harness invokes the standalone binary); `create_test_files` writes a fixture compose file into the case folder (fixed content: alpine service with `command: echo success`) — named `compose.yaml`, **except the `_f` case**, whose file name is parsed from the `-f <file>` argument in the source. `test_3_compose_cli_execution` then runs, from the case folder, `../../../../../` + `target` (the full `apptainer-compose ...` command) and then `source` (`docker-compose ...`); "same behavior" = stdout line[1] is `success` for the apptainer run and line[1] split on `" | "` → `success` for the docker run (outputs are not compared verbatim). The apptainer check runs **first**, same as above.
- **Harness contract:** the script's command line must appear in captured (piped) stdout *before* container output — hence `flush=True` in `execute()` (block-buffered print would otherwise land after the child's output).
- `tearDownClass` rewrites `status:` lines in mappings.md — but only from `test_case.evaluation` values. A failing subTest skips the assignment (stays None) → **`status: tests failed` is effectively never written automatically**; worse, if the case's *other* subTest passed, tearDownClass writes `tests passed` despite the failure (e.g. `services_service_environment`: parsing passes, execution fails → line reads `tests passed`). The status line is **not** a reliable failure indicator — judge by the suite output.

## Extension workflow — compose yaml features

1. Add the case to `mappings.md` under `## compose yaml` (`### services:\<service>:<feature>`, `status: open`, source, target).
   - Source must be a **complete, self-contained service**: image + feature + a `command:` that self-checks and prints `success`/`failure` (execution injection cannot be extended for new case ids).
   - Target must be the exact string `command_to_str` will produce (mind `K='V'` env quoting).
2. Inject parsing logic: new `state_*` function(s) + branch in `state_service` (or `state_build`); extend `command_to_list`/`command_to_str` if a CLI flag is needed.
3. Run the suite; parsing validates the string, execution validates real behavior against both apptainer and docker-compose.
4. Fix the `status:` line (auto-set to `tests passed` only when everything passes).

## Extension workflow — docker compose cli cases

1. Add the case to `mappings.md` under `## docker compose cli` (`### <name>` matching the docker CLI syntax, e.g. `### -f`, `status: open`), `source:` = the docker compose CLI command, `target:` = the equivalent `apptainer-compose` command (full form, starting with `apptainer-compose`).
2. The harness generates the fixture compose file automatically (fixed alpine service with `command: echo success`) — the case verifies the **flag routing**, not yaml features. For `-f` cases the fixture file name is derived from the source command, but **only case id `_f`** is handled in `create_test_files`; any other file-name case (e.g. `--file`) needs a harness change first.
3. Adapt `parse_args()` to accept the new flag/subcommand; if it changes the generated apptainer command or the execution flow, extend `command_to_list` / `command_to_str` / `execute`.
4. Run the suite; both `apptainer-compose <target>` and `docker-compose <source>` must print `success` on stdout line[1] from the case folder.
5. Fix the `status:` line (auto-set to `tests passed` only when everything passes).

## Environment (this WSL2 VM, user sresch, passwordless sudo, Ubuntu 26.04)

- **apptainer 1.5.3** from GitHub release `.deb` + `libfuse3-3` (3.14.0-4) from the Debian pool: Ubuntu 26.04 only ships FUSE 3.18 with SONAME `libfuse3.so.4`, while apptainer's `squashfuse_ll`/`fuse-overlayfs`/`fuse2fs` helpers need `libfuse3.so.3`. Both coexist. Works non-root (user namespaces OK in WSL2).
- **docker:** system rootful daemon (`/var/run/docker.sock`). Rootless docker is **not usable here**: the WSL2 kernel blocks all netlink device creation (bridge/veth/tap) and netfilter from user namespaces. Use `docker context use default` if a stray `rootless` context is active.
- **docker-compose:** v2.40.3 on PATH (Rancher Desktop plugin dir) — verified compatible with the harness: on stdout it emits `Attaching to <name>-1` / `<name>-1  | success` / exited line; pull progress goes to stderr. No v1 needed.
- `alpine:latest` is cached in both the system docker daemon and the apptainer cache.
- iptables backend must stay **nf_tables** (system default). Switching to legacy breaks the system dockerd's chains.

## Baseline (2026-09-02)

- 29/29 subTests pass (unittest reports `Ran 3 tests ... OK`). Implemented compose yaml cases all green: `command`, `environment` (dict **and** list form), `volumes`, `hostname` (`--hostname`), `working_dir` (`--cwd`), `dns` (`--dns`, comma-joined), `security_opt` (`no-new-privileges` → `--security no_new_privs`), `entrypoint` (service `entrypoint` → verb switches `run` → `exec`, entrypoint list prepended before the command), `labels` (accepted and ignored — apptainer has no runtime label flag), `read_only` (`false` → `--writable-tmpfs`; `true` → no flag, apptainer default), `init` (`false` → `--no-init`; `true` → no flag, apptainer default), `profiles` (profiled services skipped on `up`, still runnable via `run <service>`), top-level `version` (accepted and ignored — it broke the parser before). Docker compose cli cases green: `up`, `-f <file>`, `up <service>` (`parse_args` currently supports `-f/--file`, `-v/--verbose`, `--dry-run`; subcommands `up` [optional service names], `build`, `run`).
- Compose `$$`→`$` interpolation is applied in `command` parsing (before `shlex.split`) — this makes the harness-injected `$$FOO` self-check in `services_service_environment` pass.
- **Blacklist (persisted in mappings.md as `status: not implemented`, do not implement):** `networks` (apptainer has no container networks), `ports` (no port forwarding), `user` (no `--user` flag — `-u` is `--userns`), `tmpfs` (apptainer `--writable-tmpfs` takes no path; it is a whole-FS writable overlay), `pid` (compose only allows `pid: host`, which is already the apptainer default → vacuous), `mem_limit`/`cpus`/`cpuset` (cgroup features — `--memory`/`--cpus`/`--cpuset-*` need cgroup access, fail unprivileged: dbus "No such file or directory"), `depends_on` (apptainer is not about multi-service orchestration; a faithful mapping would require health checks and more — not worth it), security batch — `cap_add`/`cap_drop`/`privileged`/`ipc` (secondary, see Ground rules), `devices` (`--device` is CDI-only, no generic device-node passthrough), `shm_size`/`ulimits`/`sysctls`/`domainname`/`extra_hosts`/`group_add` (no corresponding apptainer flag), `tty`/`stdin_open` (auto-detected / always-on), `healthcheck`/`restart`/`stop_signal` (no runtime supervision), `logging`/`pull_policy` (no drivers; SIF caching automatic), `container_name`/`userns_mode` (no runtime naming / no userns remap config), `network_mode` (no container networks; `host` is already the default), `deploy` (cgroup + orchestration), cgroup extras `mem_reservation`/`memswap_limit`/`cpu_shares`/`cpu_quota`/`blkio_weight`/`oom_kill_disable`/`oom_score_adj` (flags exist but need cgroup access, fail unprivileged), `env_file` (untestable: frozen harness regenerates case folders with only `compose.yaml`), `volumes_from` (untestable: hard dependency on referenced service — a profiled source is rejected as undefined, and a running source breaks the harness' single-service stdout assertion; see `depends_on`), `expose` (vacuous without container networks), `links`/`external_links` (no container networks), `secrets` (file objects, untestable like `env_file`), `include`/`extends` (multi-file/cross-service composition unsupported), `isolation` (Windows-only), `dns_search`/`dns_opt` (`--dns` takes only server addresses), cgroup extras `pids_limit`/`cpu_rt_period`/`cpu_rt_runtime`/`mem_swappiness` (`--pids-limit` needs cgroup access; the rest have no flag).

## Known quirks

- **YAML engine key ordering:** a key at service level must **not** follow a nested block (`environment` / `volumes` / `dns` / `security_opt`) — `recurse`'s `continue` branch never advances the reader and the parse hangs forever (frozen engine; legacy cases avoid this by putting list-valued keys last). In mappings.md sources, list-valued keys go **last** in the service.
- `get_key_value` splits on `": "` — a `command:` value must not contain a literal colon+space (e.g. `cut -d: -f2` breaks it); self-check commands are written to avoid it.
- `Reader.is_list_item` is **sticky**: once any `- ` line is seen, every following node carries `is_list_item=True` (the frozen generator never resets it). Never use it to detect list items — use `key is None` instead.
- `working_dir` → `--cwd` requires the directory to **exist** in the image (apptainer does not create it, unlike docker).
- `hostname` values must be RFC-valid (no underscores — apptainer rejects `foo_bar` as "not a valid hostname").
- `build:` is parsed but unused in command generation (no Dockerfile→sif flow wired into `up` yet).
- `main()`: `up [service...]` executes all services, or only the named ones, sequentially (services with a non-empty `profiles` list are skipped — compose profiles have no active-profile selection yet; an explicit `run <service>` ignores profiles, matching docker); `run <service> [cmd...]` executes only that service, with `cmd` overriding its `command` (use `--` before commands that start with `-`); unknown service → error exit 1.
- No docker compose cli case for `run <service>`: `docker compose run` prints raw container stdout (no `name | ` prefix), which the harness cannot assert.
- Parsing test only checks the **first** service of a file.
- `Reader` skips any line starting with `x-` (compose extension fields) — so `x-` keys never reach the states.
- **CLI execution cases:** the harness splits both commands on single spaces (`command.split(" ")`) — arguments must not contain spaces; `target` must be the full command (the harness only prepends `../../../../../`); `create_test_files` derives a custom fixture file name **only for case id `_f`** (other file-selection flags, e.g. `--file`, would still land in `compose.yaml` and need a harness change first).
