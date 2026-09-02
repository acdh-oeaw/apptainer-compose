# apptainer-compose

\*\* experimental work in progress! \*\*

## how to use

This code contains zero dependencies and is all contained in a single python script: 
[apptainer-compose](./apptainer-compose) . 

Download it and make it executable

```
chmod +x apptainer-compose
```

And add it to your `$PATH`

## mappings

All functionalities of docker compose and whether or not they are mapped to apptainer are described 
here: [mappings.md](./mappings.md)

### acknowledgments

Some code on converting Dockerfiles to .def files was taken and modified from 
https://github.com/singularityhub/singularity-cli The relevant sections in this code 
repo are marked with 
`taken and modified from https://github.com/singularityhub/singularity-cli`
Hence, the license of this repo was also changed for sake of compliance.
