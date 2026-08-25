
## compose yaml

### mapped

- services:<service>:volumes

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

- services:<service>:command

source:
```
services:
  apptainer_compose_test:
    image: alpine:latest
    command: echo "success"
```
target:
```
apptainer run docker://alpine:latest echo "success"
```

- services:<service>:environment

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

        ### not mapped

- networks

## compose cli

### mapped

- up

source:
```
apptainer-compose -f foo.yaml up
```
target:
```
apptainer run docker://alpine:latest
```

- -f

source:
```
docker compose -f foo.yaml up
```
target:
```
apptainer-compose -f foo.yaml up
```

### not mapped

## apptainer cli

### mapped 

- --writable-tmpfs

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

### not mapped

