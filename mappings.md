
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

### networks

status: not implemented

## docker compose cli

not implemented

## apptainer cli

not implemented
