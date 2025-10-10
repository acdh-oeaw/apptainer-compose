import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apptainer_compose import parse, ParsingError


tests_target_list = [
    ("invalid_1", None),
    ("semivalid_networks", "apptainer run docker://alpine:latest"),
    ("valid_alpine", 'apptainer exec docker://alpine:latest echo "valid_alpine"'),
    (
        "valid_alpine_environment",
        "apptainer run --env var_1=bla --env var_2=true docker://alpine:latest",
    ),
    (
        "valid_alpine_volumes",
        "apptainer exec --bind ./:/mount/ --bind ./:/mount_2/ docker://alpine:latest ls /mount",
    ),
    (
        "valid_build",
        [
            "apptainer build -F valid_build.sif valid_build.def",
            "apptainer run valid_build.sif",
        ],
    ),
    (
        "valid_ghcr",
        'apptainer exec docker://ghcr.io/linuxcontainers/alpine:latest echo "valid_ghcr"',
    ),
    ("valid_veld", 'apptainer exec docker://alpine:latest echo "valid_veld"'),
]


def main_test():
    for folder, target in tests_target_list:
        print("-----------------------------------------------------------")
        print(f"{folder=}")
        os.chdir("./compose_files/" + folder)
        with open("./test.sh", "r") as f:
            command_counter = 0
            for line in f.readlines():
                sys.argv = None
                if line.startswith("../../../apptainer_compose.py"):
                    sys.argv = line.split()
                    try:
                        print(f"{sys.argv=}")
                        command, csc = parse()
                        cs = csc.compose_services[0]
                        parsed_command = cs.command_to_str(command)
                    except ParsingError as ex:
                        print(ex)
                        parsed_command = None
                    print(f"{parsed_command=}")
                    if type(target) in [str, type(None)]:
                        current_target = target
                    elif type(target) is list:
                        current_target = target[command_counter]
                    if parsed_command != current_target:
                        raise Exception(f"Error: {folder=}, {parsed_command=}, {target=}")
                    command_counter += 1
        os.chdir("../..")


if __name__ == "__main__":
    main_test()
