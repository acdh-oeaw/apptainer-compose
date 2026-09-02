
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
