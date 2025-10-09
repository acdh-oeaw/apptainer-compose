import os
import sys

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
        "valid_ghcr",
        'apptainer exec docker://ghcr.io/linuxcontainers/alpine:latest echo "valid_ghcr"',
    ),
    ("valid_veld", 'apptainer exec docker://alpine:latest echo "valid_veld"'),
]

# tests_target_list = [
# ]


def main_test():
    for folder, target in tests_target_list:
        print("-----------------------------------------------------------")
        print(f"{folder=}")
        os.chdir("./compose_files/" + folder)
        with open("./test.sh", "r") as f:
            sys.argv = None
            for line in f.readlines():
                if line.startswith("../../../apptainer_compose.py"):
                    sys.argv = line.split()
            # c = parse()
            try:
                print(f"{sys.argv=}")
                c = parse()
                cs = list(c.compose_services.values())[0]
                parsed_command = str(cs)
            except ParsingError as ex:
                print(ex)
                parsed_command = None
            print(f"{parsed_command=}")
            if parsed_command != target:
                raise Exception(f"Error: {folder=}, {parsed_command=}, {target=}")
        os.chdir("../..")


if __name__ == "__main__":
    main_test()
