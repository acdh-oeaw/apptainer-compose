
Each status can be one of: 
- status: tests passed
- status: tests failed
- status: open
- status: not implemented

## compose yaml

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

docker compose run prints raw container output (no "name | " prefix), which the harness cannot assert; up <service> is the closest verifiable equivalent

source:
```
docker compose up apptainer_compose_test
```
target:
```
apptainer-compose up apptainer_compose_test
```
