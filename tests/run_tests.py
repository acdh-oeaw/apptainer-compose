import argparse
import os
import shutil
import subprocess
import sys
import unittest
from importlib import util
from importlib.machinery import SourceFileLoader
from pathlib import Path


apptainer_main_path = Path(__file__).resolve().parent.parent / "apptainer-compose"
spec = util.spec_from_file_location("apptainer_compose", apptainer_main_path, loader=SourceFileLoader("apptainer_compose", str(apptainer_main_path)))
apptainer_compose = util.module_from_spec(spec)
spec.loader.exec_module(apptainer_compose)


def extract_test_data():
    test_data = {}
    example_section = None
    example_case = None
    example_source = None
    example_target = None
    tick_counter = 0
    with open("../mappings.md", "r") as f:
        for line in f:
            if line in ["## compose yaml\n", "## compose cli\n", "## apptainer cli\n"]:
                example_section = line[3:-1].replace(" ", "_")
                continue
            if line == "### not mapped\n":
                example_section = None
                continue
            if example_section:
                if line.startswith("- "):
                    example_case = line[2:-1].replace(":<", "_").replace(">:", "_")
            if example_case:
                if line == "source:\n":
                    example_source = ""
                    continue
                if line == "target:\n":
                    example_target = ""
                    continue
                if line == "```\n":
                    tick_counter += 1
                    if  tick_counter == 1:
                        continue
                if tick_counter == 1:
                    if example_source is not None and example_target is None:
                        example_source += line
                    if example_target is not None:
                        example_target = line[:-1]
                if tick_counter == 2:
                    tick_counter = 0
                    if example_target is not None:
                        test_data_section = test_data.get(example_section, {})
                        test_folder = "test_cases/" + example_section + "/" + example_case
                        test_data_section[example_case] = (
                            test_folder, example_source, example_target
                        )
                        test_data[example_section] = test_data_section
                        example_case = None
                        example_source = None
                        example_target = None
                    continue
    return test_data


def step_through_test_data_plan(test_data_plan):
    for test_section, test_case_dict in test_data_plan.items():
        for test_case_name, test_case_data in test_case_dict.items():
            test_case_folder, test_case_source, test_case_target = test_case_data
            yield (
                test_section,
                test_case_name,
                test_case_folder,
                test_case_source,
                test_case_target,
            )


def create_test_files(test_data_plan):
    test_case_folder_all = "./test_cases"
    shutil.rmtree(test_case_folder_all, ignore_errors=True)
    os.makedirs(test_case_folder_all)
    for test_case_data in step_through_test_data_plan(test_data_plan):
        test_section = test_case_data[0]
        test_case_folder = test_case_data[2]
        test_case_source = test_case_data[3]
        # if test_section != "compose_cli":
        if test_section == "compose_yaml":
            os.makedirs(test_case_folder)
            with open(test_case_folder + "/compose.yaml", "w") as f:
                f.write(test_case_source)


def prepare():
    test_data_plan = extract_test_data()
    create_test_files(test_data_plan)
    return test_data_plan


def print_separator():
    print("------------------------------------------")


if __name__ == "__main__":
    test_data_plan = prepare()

    class Test(unittest.TestCase):

        def parse_test(self, test_case_target):
            args = argparse.Namespace(file="compose.yaml", COMMAND="up", dry_run=True, writable_tmpfs=False)
            csc = apptainer_compose.parse_compose(args)
            cs = csc.compose_services[0]
            parsed_command = cs.command_to_str(csc.args)
            print(f"{test_case_target=}")
            print(f"{parsed_command=}")
            self.assertEqual(parsed_command, test_case_target)

        def execute_test(self, test_case_target):
            result = subprocess.run(
                ["../../../../apptainer-compose", "--dry-run", "up"],
                capture_output=True,
                text=True
            )
            output = result.stdout[:-1]
            print(f"{test_case_target=}")
            print(f"{output=}")
            self.assertEqual(output, test_case_target)

        def step_through_test_data_folder(self, test_section_selected):
            for test_case_data in step_through_test_data_plan(test_data_plan):
                test_section = test_case_data[0]
                test_case_folder = test_case_data[2]
                test_case_target= test_case_data[4]
                if test_section == test_section_selected:
                    print_separator()
                    print(f"{test_case_folder=}")
                    yield test_case_folder, test_case_target

        def test_1_compose_yaml_parsing(self):
            print_separator()
            print("test_compose_yaml_parsing")
            for test_case_folder, test_case_target in self.step_through_test_data_folder("compose_yaml"):
                os.chdir(test_case_folder)
                with self.subTest():
                    self.parse_test(test_case_target)
                os.chdir("../../../")

        def test_2_compose_yaml_execution(self):
            print_separator()
            print("test_compose_yaml_execution")
            for test_case_folder, test_case_target in self.step_through_test_data_folder("compose_yaml"):
                os.chdir(test_case_folder)
                with self.subTest():
                    self.execute_test(test_case_target)
                os.chdir("../../../")

    unittest.main()
