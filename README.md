# apptainer-compose

\*\* experimental work in progress! \*\*

## how to use

This code contains zero dependencies and is all contained in a single python script: [./apptainer_compose.py](./apptainer_compose.py) . Thus, to use it, simply download that script and use it with `python apptainer_compose.py [args]`, where `[args]` tries to be as close as possible to docker compose args, e.g. `python apptainer_compose.py up`. You may also make it executable and add it to your`$PATH`, so that you can call it anywhere with `apptainer_compose.py [args]`.

### acknowledgments

Some code on converting Dockerfiles to .def files was taken and modified from 
https://github.com/singularityhub/singularity-cli The relevant sections in this code 
repo are marked with 
`taken and modified from https://github.com/singularityhub/singularity-cli`
Hence, the license of this repo was also changed for sake of compliance.
