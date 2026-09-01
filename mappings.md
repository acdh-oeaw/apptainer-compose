
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

status: tests failed

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

status: open

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    hostname: apptainer_compose_test
    command: sh -c 'if [ "$(hostname)" = "apptainer_compose_test" ]; then echo success; else echo failure; fi'
```
target:
```
apptainer run --hostname apptainer_compose_test docker://alpine:latest sh -c if [ "$(hostname)" = "apptainer_compose_test" ]; then echo success; else echo failure; fi
```

### services:\<service>:working_dir

status: open

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

status: open

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

status: open

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

### networks

status: not implemented
