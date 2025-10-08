#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
from dataclasses import dataclass


class Command:
    image = None
    command = None
    volumes = None

    def to_list(self):
        if self.command:
            return [
                "apptainer",
                "exec",
                self.image,
            ] + self.command
        else:
            return [
                "apptainer",
                "run",
                self.image,
            ]

    def __str__(self):
        return " ".join(self.to_list())

    def __repr__(self):
        return str(self)


def validate_string(s, additional_chars=None):
    if additional_chars is None:
        additional_chars = []
    for invalid_char in [" ", ": "] + additional_chars:
        if invalid_char in s:
            raise Exception("invalid")
    return s


def get_key_and_potential_value(s):
    key = None
    value = None
    if s[-1] == ":":
        key = validate_string(s[:-1], [":"])
    else:
        key_value_list = s.split(": ")
        if len(key_value_list) != 2:
            raise Exception("invalid")
        key = validate_string(key_value_list[0])
        value = key_value_list[1].lstrip()
    return key, value


def parse_volumes(lg, c):
    for line in lg:
        pass


def state_individual_service(lg, c):
    for line in lg:
        if not (line[:4] == "    " and line[4] != " "):
            raise Exception("invalid")
        else:
            key, value = get_key_and_potential_value(line[4:])
            if key == "image":
                c.image = "docker://" + validate_string(value)
            elif key == "command":
                c.command = value.split(" ")
            elif key == "volumes":
                if value is None:
                    parse_volumes(lg, c)
    return c


def state_several_services(lg, c):
    for line in lg:
        if not (line[:2] == "  " and line[2] != " "):
            raise Exception("invalid")
        else:
            service_name, value = get_key_and_potential_value(line[2:])
            if value is not None:
                raise Exception("invalid")
            else:
                state_individual_service(lg, c)
    return c


def state_start(lg, c):
    for line in lg:
        if line.startswith("services:"):
            state_several_services(lg, c)
        elif line.startswith("#") or line.startswith("x-"):
            pass
    return c


def line_generator(file):
    with open(file, "r") as f:
        for line in f.read().splitlines():
            commented_line = False
            for char in line:
                if char == " ":
                    continue
                elif char == "#":
                    commented_line = True
                    break
                else:
                    break
            if not commented_line:
                yield line


def parse():
    parser = argparse.ArgumentParser(prog="apptainer_compose.py", description="Apptainer Compose")
    parser.add_argument("-f", "--file", help="file")

    subparsers = parser.add_subparsers(dest="COMMAND", required=True)
    subparsers.add_parser("up", help="Start services")
    subparsers.add_parser("down", help="Stop services")

    args = parser.parse_args()
    if args.file is None:
        args.file = "compose.yaml"
    print(f"COMMAND: {args.COMMAND}")
    print(f"file: {args.file}")

    return state_start(line_generator(args.file), Command())


def execute(cmd_list):
    result = subprocess.run(cmd_list)
    sys.exit(result.returncode)


def main():
    c = parse()
    print(c.to_list())
    print(c)
    execute(c.to_list())


if __name__ == "__main__":
    main()
