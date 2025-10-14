import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apptainer_compose import parse, ParsingError


tests_target_list = [
    ("invalid_1", None),
    ("semivalid_networks", 'apptainer run docker://alpine:latest echo "semivalid_networks"'),
    ("valid_alpine_command", 'apptainer run docker://alpine:latest echo "valid_alpine_command"'),
    (
        "valid_interactive_alpine_environment",
        (
            "apptainer run --env var_1='bla' --env var_2='true' --env var_3='bla ble' "
            + "--env var_4='bla ble' --env var_5='bla ble' docker://alpine:latest sh"
        ),
    ),
    (
        "valid_alpine_volumes",
        "apptainer run --bind ./:/mount/ --bind ./:/mount_2/ docker://alpine:latest ls /mount",
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
        'apptainer run docker://ghcr.io/linuxcontainers/alpine:latest echo "valid_ghcr"',
    ),
    (
        "valid_inherited_build",
        [
            "apptainer build -F ./parent/valid_inherited_build_parent.sif ./parent/valid_inherited_build_parent.def",
            "apptainer run ./parent/valid_inherited_build_parent.sif",
        ],
    ),
    (
        "valid_inherited_image",
        (
            "apptainer run --env var_parent_1='value_parent_1' --env var_parent_2='value_child_2' "
            + "--env var_child_3='value_child_3' docker://alpine:latest echo "
            + '"valid_inherited_child"'
        ),
    ),
    (
        "valid_inherited_volumes",
        (
            "apptainer run --bind ./:/out_parent_1 --bind ./parent/:/out_parent_2 "
            + "docker://alpine:latest cat /out_parent_1/compose.yaml"
        ),
    ),
    ("valid_veld", 'apptainer run docker://alpine:latest echo "valid_veld"'),
    (
        "valid_writable_tmpfs",
        "apptainer run --writable-tmpfs docker://alpine:latest touch /opt/bla",
    ),
]


def main_test(tests_target_list):
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
                        csc = parse()
                        cs = csc.compose_services[0]
                        parsed_command = cs.command_to_str(csc.args)
                    except ParsingError as ex:
                        print(ex)
                        parsed_command = None
                    if type(target) in [str, type(None)]:
                        current_target = target
                    elif type(target) is list:
                        current_target = target[command_counter]
                    if parsed_command == current_target:
                        print(f"{parsed_command=}")
                    else:
                        raise Exception(f"Error: {folder=}\n{current_target=}\n{parsed_command=}\n")
                    command_counter += 1
        os.chdir("../..")


if __name__ == "__main__":
    main_test(tests_target_list)
