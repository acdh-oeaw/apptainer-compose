
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

### up

status: open

source:
```
apptainer-compose -f foo.yaml up
```
target:
```
apptainer run docker://alpine:latest
```

### -f

status: open

source:
```
docker compose -f foo.yaml up
```
target:
```
apptainer-compose -f foo.yaml up
```

### -verbose

status: open

### --dry-run

status: open

### env vars from host

status: open

source:
```
export FOO=BAR
docker compose up
```
target:
```
apptainer-compose up
```

## apptainer cli

### --writable-tmpfs

status: open

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
apptainer --writable-tmpfs
```
