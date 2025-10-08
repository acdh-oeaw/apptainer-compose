#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
from dataclasses import dataclass


class Command:

    def __init__(self):
        self.image = None
        self.command = None
        self.volumes = []

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


class LineReader:

    def __init__(self, file_path):
        self.n = None
        self.line = None
        self.generator = self.create_generator(file_path)

    def create_generator(self, file_path):
        with open(file_path, "r") as f:
            for n, line in enumerate(f.read().splitlines(), start=1):
                skip_line = False
                char_prev = None
                for char in line:
                    if char == " ":
                        continue
                    elif char == "#":
                        skip_line = True
                        break
                    elif char_prev == "x" and char == "-":
                        skip_line = True
                        break
                    else:
                        char_prev = char
                if not skip_line:
                    yield line

    def move_to_next_line(self):
        try:
            self.n, self.line = next(self.generator)
        except:
            self.line = None

    def __str__(self):
        return f"{self.n}: {self.line}"

    def __repr__(self):
        return self.__str__()


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


def parse_volumes(lr: LineReader, c: Command):
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line[:6] == "      " and lr.line[6] == "-":
            volume_pair = lr.line[7:].lstrip().rstrip().split(":")
            if len(volume_pair) not in [2, 3]:
                raise Exception("invalid")
            else:
                volume_pair = volume_pair[:2]
                c.volumes.append(volume_pair)
        else:
            break
        lr.move_to_next_line()
    return c


def state_individual_service(lr: LineReader, c: Command):
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line[:4] == "    " and lr.line[4] != " ":
            key, value = get_key_and_potential_value(lr.line[4:])
            if key == "image":
                c.image = "docker://" + validate_string(value)
            elif key == "command":
                if c.command is not None:
                    raise Exception("invalid")
                c.command = value.split(" ")
            elif key == "volumes":
                if value is None:
                    c = parse_volumes(lr, c)
                continue
        lr.move_to_next_line()
    return c


def state_several_services(lr: LineReader, c: Command):
    lr.move_to_next_line()
    while lr.line is not None:
        if not (lr.line[:2] == "  " and lr.line[2] != " "):
            raise Exception("invalid")
        else:
            service_name, value = get_key_and_potential_value(lr.line[2:])
            if value is not None:
                raise Exception("invalid")
            else:
                c = state_individual_service(lr, c)
        lr.move_to_next_line()
    return c


def state_start(lr: LineReader, c: Command):
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line.startswith("services:"):
            c = state_several_services(lr, c)
        lr.move_to_next_line()
    return c


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

    return state_start(LineReader(args.file), Command())


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
