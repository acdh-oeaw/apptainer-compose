import argparse
import os
import shutil
import subprocess
import unittest
from importlib import util
from importlib.machinery import SourceFileLoader
from pathlib import Path


apptainer_main_path = Path(__file__).resolve().parent.parent / "apptainer-compose"
spec = util.spec_from_file_location("apptainer_compose", apptainer_main_path, loader=SourceFileLoader("apptainer_compose", str(apptainer_main_path)))
apptainer_compose = util.module_from_spec(spec)
spec.loader.exec_module(apptainer_compose)


class TestCase:
    section = None
    kind = None
    id = None
    name = None
    folder = None
    source = None
    target = None
    evaluation = None


    def __init__(
        self,
        section=None,
        kind=None,
        id=None,
        name=None,
        folder=None,
        source=None,
        target=None,
        evaluation=None,
    ):
        self.section = section
        self.kind = kind
        self.id = id
        self.name = name
        self.folder = folder
        self.source = source
        self.target = target
        self.evaluation = evaluation


test_case_list = []


def modify_compose_yaml_for_execution(example_section, example_case, example_source):
    example_source_new = example_source
    if example_section == "compose_yaml":
        example_source_split = example_source.split("\n")
        example_source_1 = "\n".join(example_source_split[:3])
        example_source_2 = "\n".join(example_source_split[3:])
        if example_case == "services_service_command":
            example_source_new = example_source
        elif example_case == "services_service_environment":
            example_source_new = (
                example_source_1
                + '\n    command: sh -c \'if [ "$$FOO" = "BAR" ]; then echo "success"; else echo "failure"; fi\'\n'
                + example_source_2
            )
        elif example_case == "services_service_volumes":
            example_source_new = (
                example_source_1
                + '\n    command: sh -c \'if [ -f "/foo/compose.yaml" ]; then echo "success"; else echo "failure"; fi\'\n'
                + example_source_2
            )
    return example_source_new


def create_test_case_data(
    example_section,
    example_case_id,
    example_case_name,
    example_source,
    example_target,
):
    for kind in ["parsing", "execution"]:
        test_folder_parsing = "test_cases/" + example_section + "/" + kind + "/" + example_case_id
        if kind == "execution":
            example_source = modify_compose_yaml_for_execution(
                example_section,
                example_case_id,
                example_source,
            )
        test_case_list.append(TestCase(
            section=example_section,
            kind=kind,
            id=example_case_id,
            name=example_case_name,
            folder=test_folder_parsing,
            source=example_source,
            target=example_target,
        ))

def extract_test_data():
    example_section = None
    example_case_id = None
    example_case_name = None
    example_source = None
    example_target = None
    tick_counter = 0
    with open("../mappings.md", "r") as f:
        for line in f:
            if line in ["## compose yaml\n", "## compose cli\n", "## apptainer cli\n"]:
                example_section = line[3:-1].replace(" ", "_")
                continue
            if example_section:
                if line.startswith("### "):
                    example_case_name = line
                    example_case_id = line[4:-1].replace(":\\<", "_").replace(">:", "_")
            if example_case_id:
                if line.startswith("status: "):
                    if line.endswith("not implemented"):
                        continue
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
                        create_test_case_data(
                            example_section,
                            example_case_id,
                            example_case_name,
                            example_source,
                            example_target,
                        )
                        example_case_id = None
                        example_source = None
                        example_target = None
                    continue


def create_test_files():
    test_case_folder_all = "./test_cases"
    shutil.rmtree(test_case_folder_all, ignore_errors=True)
    os.makedirs(test_case_folder_all)
    for test_case in test_case_list:
        if test_case.section == "compose_yaml":
            os.makedirs(test_case.folder)
            with open(test_case.folder + "/compose.yaml", "w") as f:
                f.write(test_case.source)


def print_separator(title=None):
    print("------------------------------------------")
    if title is not None:
        print(title)


class Test(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        extract_test_data()
        create_test_files()


    def evaluate_and_assert(self, source, target):
        evaluation = source == target
        if evaluation:
            print("success")
        else:
            print("failure")
        self.assertTrue(evaluation)
        return evaluation


    def parse_test(self, test_case_target):
        args = argparse.Namespace(file="compose.yaml", COMMAND="up", dry_run=True, writable_tmpfs=False)
        csc = apptainer_compose.parse_compose(args)
        cs = csc.compose_services[0]
        parsed_command = cs.command_to_str(csc.args)
        print(f"{test_case_target=}")
        print(f"{parsed_command=}")
        return self.evaluate_and_assert(parsed_command, test_case_target)


    def execute_apptainer(self):
        result = subprocess.run(
            ["../../../../../apptainer-compose", "up"],
            capture_output=True,
            text=True
        )
        print(f"{result.stderr=}")
        print(f"{result.stdout=}")
        outcome = result.stdout.split("\n")[1]
        return self.evaluate_and_assert(outcome, "success")


    def execute_docker(self):
        result = subprocess.run(
            ["docker-compose", "up"],
            capture_output=True,
            text=True
        )
        print(f"{result.stderr=}")
        print(f"{result.stdout=}")
        out_split = result.stdout.split("\n")
        outcome = out_split[1].split(" | ")[1]
        return self.evaluate_and_assert(outcome, "success")


    def execute_test(self):
        evaluation_1 = self.execute_apptainer()
        evaluation_2 = self.execute_docker()
        return evaluation_1 and evaluation_2


    def step_through_and_execute_tests(self, test_section_selected, test_kind_selected):
        for test_case in test_case_list:
            if test_case.section == test_section_selected and test_case.kind == test_kind_selected:
                print_separator(test_case.folder)
                os.chdir(test_case.folder)
                with self.subTest():
                    if test_kind_selected == "parsing":
                        test_case.evaluation = self.parse_test(test_case.target)
                    elif test_kind_selected == "execution":
                        test_case.evaluation = self.execute_test()
                os.chdir("../../../../")


    def test_1_compose_yaml_parsing(self):
        print_separator("test_1_compose_yaml_parsing")
        self.step_through_and_execute_tests("compose_yaml", "parsing")


    def test_2_compose_yaml_execution(self):
        print_separator("test_2_compose_yaml_execution")
        self.step_through_and_execute_tests("compose_yaml", "execution")


    @classmethod
    def tearDownClass(cls):
        content = ""
        with open("../mappings.md", "r") as f:
            has_test_result = False
            for line in f:
                if line.startswith("### "):
                    content += line
                    all_test_passed = None
                    for test_case in test_case_list:
                        if line == test_case.name:
                            if test_case.evaluation is not None:
                                if all_test_passed is None:
                                    all_test_passed = test_case.evaluation
                                else:
                                    all_test_passed = all_test_passed and test_case.evaluation
                    if all_test_passed is not None:
                        has_test_result = True
                elif has_test_result and line.startswith("status: "):
                    if all_test_passed:
                        content += "status: tests passed\n"
                    else:
                        content += "status: tests failed\n"
                    has_test_result = False
                else:
                    content += line
        with open("../mappings.md", "w") as f:
            f.write(content)
