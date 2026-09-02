
Three sets of functionalities are mapped and described here:

- [compose yaml](#compose-yaml)
- [docker compose cli](#docker-compose-cli)
- [apptainer cli](#apptainer-cli)

Within each set is a list of features, their statuses, and an example mapping.

Each status can be one of: 

- status: tests passed
- status: tests failed
- status: open
- status: not implemented

## compose yaml

This set covers the contents of docker compose yaml files and what their mapped
`apptainer-compose` equivalents are.

### services:\<service>:volumes

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    volumes:
      - ./:/foo
```
target:
```
apptainer run --bind ./:/foo docker://alpine:latest
```

### services:\<service>:command

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    command: echo success
```
target:
```
apptainer run docker://alpine:latest echo success
```

### services:\<service>:environment

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    environment:
      FOO: "BAR"
```
target:
```
apptainer run --env FOO='BAR' docker://alpine:latest
```

### services:\<service>:hostname

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    hostname: apptainer-compose-test
    command: sh -c 'if [ "$(hostname)" = "apptainer-compose-test" ]; then echo success; else echo failure; fi'
```
target:
```
apptainer run --hostname apptainer-compose-test docker://alpine:latest sh -c if [ "$(hostname)" = "apptainer-compose-test" ]; then echo success; else echo failure; fi
```

### services:\<service>:working_dir

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    working_dir: /var
    command: sh -c 'if [ "$(pwd)" = "/var" ]; then echo success; else echo failure; fi'
```
target:
```
apptainer run --cwd /var docker://alpine:latest sh -c if [ "$(pwd)" = "/var" ]; then echo success; else echo failure; fi
```

### services:\<service>:dns

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    command: sh -c 'if grep -q "1.1.1.1" /etc/resolv.conf && grep -q "8.8.8.8" /etc/resolv.conf; then echo success; else echo failure; fi'
    dns:
      - 1.1.1.1
      - 8.8.8.8
```
target:
```
apptainer run --dns 1.1.1.1,8.8.8.8 docker://alpine:latest sh -c if grep -q "1.1.1.1" /etc/resolv.conf && grep -q "8.8.8.8" /etc/resolv.conf; then echo success; else echo failure; fi
```

### services:\<service>:security_opt

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    command: sh -c 'if grep -Eq "NoNewPrivs:[[:space:]]1" /proc/self/status; then echo success; else echo failure; fi'
    security_opt:
      - no-new-privileges
```
target:
```
apptainer run --security no_new_privs docker://alpine:latest sh -c if grep -Eq "NoNewPrivs:[[:space:]]1" /proc/self/status; then echo success; else echo failure; fi
```

### services:\<service>:entrypoint

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    entrypoint: sh
    command: -c 'if [ -n "$$0" ]; then echo success; else echo failure; fi'
```
target:
```
apptainer exec docker://alpine:latest sh -c if [ -n "$0" ]; then echo success; else echo failure; fi
```

### services:\<service>:labels

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    command: echo success
    labels:
      com.example.apptainer-compose: test
```
target:
```
apptainer run docker://alpine:latest echo success
```

### services:\<service>:environment_list

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    command: sh -c 'if [ "$$FOO" = "BAR" ]; then echo success; else echo failure; fi'
    environment:
      - FOO=BAR
```
target:
```
apptainer run --env FOO='BAR' docker://alpine:latest sh -c if [ "$FOO" = "BAR" ]; then echo success; else echo failure; fi
```

### services:\<service>:read_only

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    read_only: false
    command: sh -c 'if touch /tmp/x; then echo success; else echo failure; fi'
```
target:
```
apptainer run --writable-tmpfs docker://alpine:latest sh -c if touch /tmp/x; then echo success; else echo failure; fi
```

### services:\<service>:init

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    init: false
    command: echo success
```
target:
```
apptainer run --no-init docker://alpine:latest echo success
```

### version

status: tests passed

source:
```
version: "3.8"
services:
  apptainer_compose_test:
    image: alpine:latest
    command: echo success
```
target:
```
apptainer run docker://alpine:latest echo success
```

<details>
<summary>not implemented</summary>

### networks

status: not implemented

apptainer does not support container networks

### ports

status: not implemented

apptainer does not support forwardinng ports

### user

status: not implemented

apptainer cannot set the user inside the container (no --user flag; -u is --userns)

### tmpfs

status: not implemented

apptainer --writable-tmpfs takes no path (it makes the whole file system writable), so individual tmpfs mounts cannot be mapped

### pid

status: not implemented

compose only allows pid: host, which is already apptainer's default, so there is nothing to map

### mem_limit

status: not implemented

apptainer --memory requires cgroup access, which fails unprivileged (dbus: No such file or directory)

### cpus

status: not implemented

apptainer --cpus requires cgroup access, which fails unprivileged (dbus: No such file or directory)

### cpuset

status: not implemented

apptainer --cpuset-cpus/--cpuset-mems require cgroup access, which fails unprivileged (dbus: No such file or directory)

### depends_on

status: not implemented

apptainer is not about multi service orchestration; a faithful mapping would require health checks and more, which is not worth it

### cap_add

status: not implemented

apptainer does not aim for full isolation like docker; capability management is secondary and not mapped

### cap_drop

status: not implemented

apptainer does not aim for full isolation like docker; capability management is secondary and not mapped

### privileged

status: not implemented

apptainer does not aim for full isolation like docker; there is no --privileged equivalent (security is secondary)

### ipc

status: not implemented

apptainer does not aim for full isolation like docker; IPC namespace control (--ipc) is secondary and not mapped, host IPC is already the default

### devices

status: not implemented

apptainer --device only accepts fully-qualified CDI device names (<vendor>/<class>=<name> with a CDI spec), not generic host device nodes like docker devices:

### shm_size

status: not implemented

apptainer has no flag to size /dev/shm

### ulimits

status: not implemented

apptainer has no ulimit flags

### sysctls

status: not implemented

apptainer has no sysctl flags (would need host kernel access)

### tty

status: not implemented

apptainer has no TTY allocation flag; TTY use is detected automatically from the session

### stdin_open

status: not implemented

apptainer always passes stdin through and has no detached mode, so there is nothing to map

### domainname

status: not implemented

apptainer has no --domainname flag

### extra_hosts

status: not implemented

apptainer has no --add-host flag

### healthcheck

status: not implemented

apptainer has no runtime health checks

### logging

status: not implemented

apptainer has no logging drivers; output goes to the terminal

### pull_policy

status: not implemented

apptainer has no pull policy flag; SIF caching is automatic

### restart

status: not implemented

apptainer runs one-shot; there is no restart policy or supervision

### container_name

status: not implemented

apptainer has no container naming at runtime

### group_add

status: not implemented

apptainer has no --group-add flag

### userns_mode

status: not implemented

apptainer has no user namespace remapping configuration (-u/--userns is a different thing)

### stop_signal

status: not implemented

apptainer has no process supervision or stop signaling (stop_signal/stop_grace_period)

### deploy

status: not implemented

resources limits are cgroup features (see mem_limit/cpus/cpuset); replicas and restart_policy are orchestration (see depends_on)

### env_file

status: not implemented

apptainer has --env-file, but the frozen harness cannot test it: case folders are regenerated with only compose.yaml, so a referenced env file cannot exist

### network_mode

status: not implemented

apptainer has no container networks (see networks); network_mode: host is already the default

### mem_reservation, memswap_limit, cpu_shares, cpu_quota, blkio_weight, oom_kill_disable, oom_score_adj

status: not implemented

cgroup features; the flags exist (--memory-reservation, --memory-swap, --cpu-shares, --blkio-weight, --oom-kill-disable) but need cgroup access, which fails unprivileged (like mem_limit/cpus/cpuset)

### volumes_from

status: not implemented

creates a hard dependency on the referenced service (apptainer rejects a profiled source as undefined), and a second running service breaks the test harness' single-service stdout assertion; see depends_on

### expose

status: not implemented

vacuous without container networks: it only documents ports between linked containers (see networks/links)

### links, external_links

status: not implemented

apptainer has no container networks or inter-container linking (see networks)

### secrets

status: not implemented

file objects, and the frozen harness regenerates case folders with only compose.yaml, so referenced secret files cannot exist (like env_file)

### include, extends

status: not implemented

multi-file / cross-service composition; the converter parses a single self-contained compose file

### isolation

status: not implemented

Windows-only compose concept (process/hyperv); apptainer on Linux has no equivalent

### dns_search, dns_opt

status: not implemented

apptainer --dns accepts only server addresses, not search domains or options

### pids_limit, cpu_rt_period, cpu_rt_runtime, mem_swappiness

status: not implemented

cgroup features; --pids-limit exists but needs cgroup access (fails unprivileged, like mem_limit/cpus/cpuset), and the cpu_rt_*/mem_swappiness options have no apptainer flag at all

### services:\<service>:profiles

status: not implemented

More of an orchestration feature, with less relevance for apptainer

</details>

## docker compose cli

This set covers functionalities of the `docker compose` CLI and their 
`apptaincer-compose` equivalents.

### up

status: tests passed

source:
```
docker compose up
```
target:
```
apptainer-compose up
```

### -f

status: tests passed

source:
```
docker compose -f foo.yaml up
```
target:
```
apptainer-compose -f foo.yaml up
```

### up\<service>

status: tests passed

source:
```
docker compose up apptainer_compose_test
```
target:
```
apptainer-compose up apptainer_compose_test
```

### -p

status: open

source:
```
docker compose -p foo up
```
target:
```
apptainer-compose -p foo up
```

### --project-directory

status: tests passed

source:
```
docker compose --project-directory . up
```
target:
```
apptainer-compose --project-directory . up
```

### --ansi

status: tests passed

source:
```
docker compose --ansi never up
```
target:
```
apptainer-compose --ansi never up
```

### --parallel

status: tests passed

source:
```
docker compose --parallel 1 up
```
target:
```
apptainer-compose --parallel 1 up
```

### --compatibility

status: tests passed

source:
```
docker compose --compatibility up
```
target:
```
apptainer-compose --compatibility up
```

### --all-resources

status: tests passed

source:
```
docker compose --all-resources up
```
target:
```
apptainer-compose --all-resources up
```

### --pull

status: tests passed

source:
```
docker compose up --pull never
```
target:
```
apptainer-compose up --pull never
```

### --quiet-pull

status: tests passed

source:
```
docker compose up --quiet-pull
```
target:
```
apptainer-compose up --quiet-pull
```

### --build

status: tests passed

source:
```
docker compose up --build
```
target:
```
apptainer-compose up --build
```

### --no-build

status: tests passed

source:
```
docker compose up --no-build
```
target:
```
apptainer-compose up --no-build
```

### --quiet-build

status: tests passed

source:
```
docker compose up --quiet-build
```
target:
```
apptainer-compose up --quiet-build
```

### --abort-on-container-exit

status: tests passed

source:
```
docker compose up --abort-on-container-exit
```
target:
```
apptainer-compose up --abort-on-container-exit
```

### --abort-on-container-failure

status: tests passed

source:
```
docker compose up --abort-on-container-failure
```
target:
```
apptainer-compose up --abort-on-container-failure
```

### --exit-code-from

status: tests passed

source:
```
docker compose up --exit-code-from apptainer_compose_test
```
target:
```
apptainer-compose up --exit-code-from apptainer_compose_test
```

### --no-color

status: tests passed

source:
```
docker compose up --no-color
```
target:
```
apptainer-compose up --no-color
```

### --no-deps

status: tests passed

source:
```
docker compose up --no-deps
```
target:
```
apptainer-compose up --no-deps
```

### --no-recreate

status: tests passed

source:
```
docker compose up --no-recreate
```
target:
```
apptainer-compose up --no-recreate
```

### --force-recreate

status: tests passed

source:
```
docker compose up --force-recreate
```
target:
```
apptainer-compose up --force-recreate
```

### --always-recreate-deps

status: tests passed

source:
```
docker compose up --always-recreate-deps
```
target:
```
apptainer-compose up --always-recreate-deps
```

### --remove-orphans

status: tests passed

source:
```
docker compose up --remove-orphans
```
target:
```
apptainer-compose up --remove-orphans
```

### -V

status: tests passed

source:
```
docker compose up -V
```
target:
```
apptainer-compose up -V
```

### -t

status: tests passed

source:
```
docker compose up -t 5
```
target:
```
apptainer-compose up -t 5
```

### -y

status: tests passed

source:
```
docker compose up -y
```
target:
```
apptainer-compose up -y
```

### --attach

status: tests passed

source:
```
docker compose up --attach apptainer_compose_test
```
target:
```
apptainer-compose up --attach apptainer_compose_test
```

### --no-attach

status: tests passed

source:
```
docker compose up --no-attach apptainer_compose_test
```
target:
```
apptainer-compose up --no-attach apptainer_compose_test
```

### --scale

status: tests passed

source:
```
docker compose up --scale apptainer_compose_test=1
```
target:
```
apptainer-compose up --scale apptainer_compose_test=1
```

### --profile

status: not implemented

activates compose profiles; the profiles feature itself is blacklisted in the compose yaml section, so there is nothing to select

### --menu

status: not implemented

interactive TTY feature; non-interactive stdout is unreliable (success line sometimes missing), so the harness cannot assert it. The flag itself is accepted by `parse_args` for drop-in compatibility

<details>
<summary>not implemented</summary>

### --dry-run

status: not implemented

`docker compose up --dry-run` is rejected in v2.40 ("interactive run is not supported in dry-run mode"), so it is untestable. `apptainer-compose --dry-run` is its own, working flag

### --env-file

status: not implemented

untestable: the file must exist in the case folder, but the frozen harness only writes `compose.yaml`

### --timestamps

status: not implemented

untestable: prefixes the success line with a timestamp, breaking the harness' ` | success` assertion

### -d

status: not implemented

untestable: detached mode prints no ` | success` line to stdout

### --wait

status: not implemented

untestable: implies detached mode and errors when the service exits (the fixture exits immediately)

### --no-start

status: not implemented

untestable: containers are created but never started, so no ` | success` line

### --no-log-prefix

status: not implemented

untestable: removes the `name | ` prefix the harness asserts on

### -w

status: not implemented

untestable: watch mode never exits

### run

status: not implemented

untestable: `docker compose run` prints raw container stdout without the `name | ` prefix the harness asserts on. The subcommand itself is accepted by `parse_args` for drop-in compatibility

### start, stop, restart, pause, unpause, down, kill, rm

status: not implemented

lifecycle of persistent containers, which apptainer has none of (one-shot runs); no ` | success` line on stdout

### ps, logs, top, stats, events, ls, images, volumes

status: not implemented

inspection of running projects/containers, which apptainer has none of; no ` | success` line on stdout

### pull, config, version

status: not implemented

print non-container output (pull status / rendered yaml / version string); no ` | success` line on stdout. SIF caching is automatic in apptainer

### exec, create, cp, export, commit

status: not implemented

operations on persistent containers, which apptainer has none of (one-shot runs)

### port

status: not implemented

no port forwarding (`ports` is blacklisted in the compose yaml section)

### scale

status: not implemented

no multi-instance orchestration

### bridge, publish

status: not implemented

no apptainer counterpart

</details>

## apptainer cli

This set covers functionalities of the apptainer CLI and how they are
represented within compose yaml files with the `x-apptainer` key. Note that
the `apptainer-compose` CLI does not support any `apptainer` CLI features
as some conflict with the `docker compose` CLI.

### --writable-tmpfs

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - writable-tmpfs
```
target:
```
apptainer run --writable-tmpfs docker://alpine:latest
```

### --cleanenv

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - cleanenv
```
target:
```
apptainer run --cleanenv docker://alpine:latest
```

### --compat

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - compat
```
target:
```
apptainer run --compat docker://alpine:latest
```

### --contain

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - contain
```
target:
```
apptainer run --contain docker://alpine:latest
```

### --containall

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - containall
```
target:
```
apptainer run --containall docker://alpine:latest
```

### --disable-cache

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - disable-cache
```
target:
```
apptainer run --disable-cache docker://alpine:latest
```

### --fakeroot

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - fakeroot
```
target:
```
apptainer run --fakeroot docker://alpine:latest
```

### --intel-hpu

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - intel-hpu
```
target:
```
apptainer run --intel-hpu docker://alpine:latest
```

### --ipc

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - ipc
```
target:
```
apptainer run --ipc docker://alpine:latest
```

### --no-eval

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-eval
```
target:
```
apptainer run --no-eval docker://alpine:latest
```

### --no-home

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-home
```
target:
```
apptainer run --no-home docker://alpine:latest
```

### --no-https

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-https
```
target:
```
apptainer run --no-https docker://alpine:latest
```

### --no-init

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-init
```
target:
```
apptainer run --no-init docker://alpine:latest
```

### --no-pid

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-pid
```
target:
```
apptainer run --no-pid docker://alpine:latest
```

### --no-privs

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-privs
```
target:
```
apptainer run --no-privs docker://alpine:latest
```

### --no-umask

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - no-umask
```
target:
```
apptainer run --no-umask docker://alpine:latest
```

### --nv

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - nv
```
target:
```
apptainer run --nv docker://alpine:latest
```

### --pid

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - pid
```
target:
```
apptainer run --pid docker://alpine:latest
```

### --rocm

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - rocm
```
target:
```
apptainer run --rocm docker://alpine:latest
```

### --unsquash

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - unsquash
```
target:
```
apptainer run --unsquash docker://alpine:latest
```

### --userns

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - userns
```
target:
```
apptainer run --userns docker://alpine:latest
```

### --uts

status: tests passed

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    x-apptainer:
      - uts
```
target:
```
apptainer run --uts docker://alpine:latest
```

<details><summary>not implemented</summary>

Single-word `apptainer run` flags that are valid CLI options but not mapped via
`x-apptainer`, with the reason:

- `--help` — meta flag, prints help and exits instead of running a container.
- `--net` — container networking (bridge network), out of scope (apptainer has no container networks; see the `networks` blacklist).
- `--passphrase` — interactive prompt (encryption passphrase), would hang automated execution.
- `--docker-login` — interactive prompt (registry login), would hang automated execution.
- `--allow-setuid` — root only, cannot work flawlessly unprivileged.
- `--keep-privs` — root only, cannot work flawlessly unprivileged.
- `--nvccli` — requires the `nvidia-container-cli` binary for GPU setup, not installed here.
- `--oom-kill-disable` — cgroup feature, needs cgroup/dbus access, fails unprivileged (like the blacklisted cgroup features).
- `--sharens` — cgroup feature, needs cgroup/dbus access, fails unprivileged (like the blacklisted cgroup features).
- `--writable` — needs a SIF with a writable overlay partition; `docker://` images (converted on the fly) have none. Use `--writable-tmpfs` instead (already mapped).

</details>
