#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import warnings
from argparse import Namespace
from collections.abc import Generator
from copy import deepcopy


# - Dockerfile converter ---------------------------------------------------------------------------


class Recipe:
    """
    taken and modified from https://github.com/singularityhub/singularity-cli

    source of class:
    https://github.com/singularityhub/singularity-cli/blob/master/spython/main/parse/recipe.py

    a recipe includes an environment, labels, runscript or command,
    and install sequence. This object is interacted with by a Parser
    (intended to popualte the recipe with content) and a Writer (intended
    to write a recipe to file). The parsers and writers are located in
    parsers.py, and writers.py, respectively. The user is also free to use
    the recipe class to build recipes.

    Parameters
    ==========
    recipe: the original recipe file, parsed by the subclass either
            DockerParser or SingularityParser
    layer: the count of the layer, for human readability

    """

    def __init__(self, recipe=None, layer=1):
        self.cmd = None
        self.comments = []
        self.entrypoint = None
        self.environ = []
        self.files = []
        self.layer_files = {}
        self.install = []
        self.labels = []
        self.ports = []
        self.test = None
        self.volumes = []
        self.workdir = None
        self.layer = layer
        self.fromHeader = None

        self.source = recipe

    def __str__(self):
        """show the user the recipe object, along with the type. E.g.,

        [spython-recipe][source:Singularity]
        [spython-recipe][source:Dockerfile]

        """
        base = "[spython-recipe]"
        if self.source:
            base = "%s[source:%s]" % (base, self.source)
        return base

    def json(self):
        """return a dictionary version of the recipe, intended to be parsed
        or printed as json.

        Returns: a dictionary of attributes including cmd, comments,
                 entrypoint, environ, files, install, labels, ports,
                 test, volumes, and workdir, organized by layer for
                 multistage builds.
        """
        attributes = [
            "cmd",
            "comments",
            "entrypoint",
            "environ",
            "files",
            "fromHeader",
            "layer_files",
            "install",
            "labels",
            "ports",
            "test",
            "volumes",
            "workdir",
        ]

        result = {}

        for attrib in attributes:
            value = getattr(self, attrib)
            if value:
                result[attrib] = value

        return result

    def __repr__(self):
        return self.__str__()


class DockerParser:
    """
    taken and modified from https://github.com/singularityhub/singularity-cli

    source of class:
    https://github.com/singularityhub/singularity-cli/blob/master/spython/main/parse/parsers/base.py
    https://github.com/singularityhub/singularity-cli/blob/master/spython/main/parse/parsers/docker.py
    """

    name = "docker"

    def __init__(self, filename="Dockerfile", load=True):
        """a generic recipe parser holds the original file, and provides
        shared functions for interacting with files. If the subclass has
        a parse function defined, we parse the filename

        Parameters
        ==========
        filename: the recipe file to parse.
        load: if True, load the filename into the Recipe. If not loaded,
              the user can call self.parse() at a later time.

        """
        self.filename = filename
        self._run_checks()
        self.lines = []

        # Arguments can be used internally, active layer name and number
        self.args = {}
        self.active_layer = "spython-base"
        self.active_layer_num = 1

        # Support multistage builds
        self.recipe = {"spython-base": Recipe(self.filename)}

        if self.filename:
            # Read in the raw lines of the file
            with open(self.filename, "r") as filey:
                self.lines = filey.readlines()

            # If parsing function defined, parse the recipe
            if load:
                self.parse()

    def __str__(self):
        """show the user the recipe object, along with the type. E.g.,

        [spython-parser][docker]
        [spython-parser][singularity]

        """
        base = "[spython-parser]"
        if hasattr(self, "name"):
            base = "%s[%s]" % (base, self.name)
        return base

    def __repr__(self):
        return self.__str__()

    def _run_checks(self):
        """basic sanity checks for the file name (and others if needed) before
        attempting parsing.
        """
        if self.filename is not None:
            # Does the recipe provided exist?
            if not os.path.exists(self.filename):
                print("Cannot find %s, is the path correct?" % self.filename)
                sys.exit(1)

            # Ensure we carry fullpath
            self.filename = os.path.abspath(self.filename)

    def _split_line(self, line):
        """clean a line to prepare it for parsing, meaning separation
        of commands. We remove newlines (from ends) along with extra spaces.

        Parameters
        ==========
        line: the string to parse into parts

        Returns
        =======
        parts: a list of line pieces, the command is likely first

        """
        return [x.strip() for x in line.split(" ", 1)]

    def _multistage(self, fromHeader):
        """Given a from header, determine if we have a multistage build, and
        update the recipe parser active in case that we do. If we are dealing
        with the first layer and it's named, we also update the default
        name "spython-base" to be what the recipe intended.

        Parameters
        ==========
        fromHeader: the fromHeader parsed from self.from, possibly with AS
        """
        # Derive if there is a named layer
        match = re.search("AS (?P<layer>.+)", fromHeader, flags=re.I)
        if match:
            layer = match.groups("layer")[0].strip()

            # If it's the first layer named incorrectly, we need to rename
            if len(self.recipe) == 1 and list(self.recipe)[0] == "spython-base":
                self.recipe[layer] = deepcopy(self.recipe[self.active_layer])
                del self.recipe[self.active_layer]
            else:
                self.active_layer_num += 1
                self.recipe[layer] = Recipe(self.filename, self.active_layer_num)
            self.active_layer = layer
            print("Active layer #%s updated to %s" % (self.active_layer_num, self.active_layer))

    def _replace_from_dict(self, string, args):
        """Given a lookup of arguments, args, replace any that are found in
        the given string. This is intended to be used to substitute ARGs
        provided in a Dockerfile into other sections, e.g., FROM $BASE

        Parameters
        ==========
        string: an input string to look for replacements
        args: a dictionary to make lookups from

        Returns
        =======
        string: the string with replacements made
        """
        for key, value in args.items():
            if re.search("([$]" + key + "|[$][{]" + key + "[}])", string):
                string = re.sub("([$]" + key + "|[$]{" + key + "[}])", value, string)
        return string

    def parse(self):
        """parse is the base function for parsing the Dockerfile, and extracting
        elements into the correct data structures. Everything is parsed into
        lists or dictionaries that can be assembled again on demand.

        Environment: Since Docker also exports environment as we go,
                     we add environment to the environment section and
                     install

        Labels: include anything that is a LABEL, ARG, or (deprecated)
                maintainer.

        Add/Copy: are treated the same

        """
        parser = None
        previous = None

        for line in self.lines:
            parser = self._get_mapping(line, parser, previous)

            # Parse it, if appropriate
            if parser:
                parser(line)

            previous = line

        # Instantiated by ParserBase
        return self.recipe

    # Setup for each Parser

    def _setup(self, action, line):
        """replace the command name from the group, alert the user of content,
        and clean up empty spaces
        """
        print("[in]  %s" % line)

        # Replace ACTION at beginning
        line = re.sub("^%s" % action, "", line)

        # Handle continuation lines without ACTION by padding with leading space
        line = " " + line

        # Split into components
        return [x for x in self._split_line(line) if x not in ["", None]]

    # From Parser

    def _from(self, line):
        """get the FROM container image name from a FROM line. If we have
        already seen a FROM statement, this is indicative of adding
        another image (multistage build).

        Parameters
        ==========
        line: the line from the recipe file to parse for FROM
        recipe: the recipe object to populate.
        """
        fromHeader = self._setup("FROM", line)

        # Do we have a multistge build to update the active layer?
        self._multistage(fromHeader[0])

        # Now extract the from header, make args replacements
        self.recipe[self.active_layer].fromHeader = self._replace_from_dict(
            re.sub("AS .+", "", fromHeader[0], flags=re.I), self.args
        )

        if "scratch" in self.recipe[self.active_layer].fromHeader:
            print("scratch is no longer available on Docker Hub.")
        print("FROM %s" % self.recipe[self.active_layer].fromHeader)

    # Run and Test Parser

    def _run(self, line):
        """everything from RUN goes into the install list

        Parameters
        ==========
        line: the line from the recipe file to parse for FROM

        """
        line = self._setup("RUN", line)
        self.recipe[self.active_layer].install += line

    def _test(self, line):
        """A healthcheck is generally a test command

        Parameters
        ==========
        line: the line from the recipe file to parse for FROM

        """
        self.recipe[self.active_layer].test = self._setup("HEALTHCHECK", line)

    # Arg Parser

    def _arg(self, line):
        """singularity doesn't have support for ARG, so instead will issue
        a warning to the console for the user to export the variable
        with SINGULARITY prefixed at build.

        Parameters
        ==========
        line: the line from the recipe file to parse for ARG

        """
        line = self._setup("ARG", line)

        # Args are treated like envars, so we add them to install
        environ = self.parse_env([x for x in line if "=" in x])
        self.recipe[self.active_layer].install += environ

        # Try to extract arguments from the line
        for arg in line:
            # An undefined arg cannot be used
            if "=" not in arg:
                print(
                    "ARG is not supported for Singularity, and must be defined with "
                    "a default to be parsed. Skipping %s" % arg
                )
                continue

            arg, value = arg.split("=", 1)
            arg = arg.strip()
            value = value.strip()
            print("Updating ARG %s to %s" % (arg, value))
            self.args[arg] = value

    # Env Parser

    def _env(self, line):
        """env will parse a line that beings with ENV, indicative of one or
        more environment variables.

        Parameters
        ==========
        line: the line from the recipe file to parse for ADD

        """
        line = self._setup("ENV", line)

        # Extract environment (list) from the line
        environ = self.parse_env(line)

        # Add to global environment, run during install
        self.recipe[self.active_layer].install += environ

        # Also define for global environment
        self.recipe[self.active_layer].environ += environ

    def parse_env(self, envlist):
        """parse_env will parse a single line (with prefix like ENV removed) to
        a list of commands in the format KEY=VALUE For example:

        ENV PYTHONBUFFER 1 --> [PYTHONBUFFER=1]
        Docker: https://docs.docker.com/engine/reference/builder/#env
        """
        if not isinstance(envlist, list):
            envlist = [envlist]

        exports = []

        for env in envlist:
            pieces = re.split("( |\\\".*?\\\"|'.*?')", env)
            pieces = [p for p in pieces if p.strip()]

            while pieces:
                current = pieces.pop(0)

                if current.endswith("="):
                    # Case 1: ['A='] --> A=
                    nextone = ""

                    # Case 2: ['A=', '"1 2"'] --> A=1 2
                    if pieces:
                        nextone = pieces.pop(0)
                    exports.append("%s%s" % (current, nextone))

                # Case 3: ['A=B']     --> A=B
                elif "=" in current:
                    exports.append(current)

                # Case 4: ENV \\
                elif current.endswith("\\"):
                    continue

                # Case 5: ['A', 'B']  --> A=B
                else:
                    nextone = pieces.pop(0)
                    exports.append("%s=%s" % (current, nextone))

        return exports

    # Add and Copy Parser

    def _copy(self, lines):
        """parse_add will copy multiple files from one location to another.
        This likely will need tweaking, as the files might need to be
        mounted from some location before adding to the image.
        The add command is done for an entire directory. It is also
        possible to have more than one file copied to a destination:
        https://docs.docker.com/engine/reference/builder/#copy
        e.g.: <src> <src> <dest>/
        """
        lines = self._setup("COPY", lines)

        for line in lines:
            # Take into account multistage builds
            layer = None
            if line.startswith("--from"):
                layer = line.strip("--from").split(" ")[0].lstrip("=")
                if layer not in self.recipe:
                    print("COPY requested from layer %s, but layer not previously defined." % layer)
                    continue

                # Remove the --from from the line
                line = " ".join([word for word in line.split(" ")[1:] if word])

            values = line.split(" ")
            topath = values.pop()
            for frompath in values:
                self._add_files(frompath, topath, layer)

    def _add(self, lines):
        """Add can also handle https, and compressed files.

        Parameters
        ==========
        line: the line from the recipe file to parse for ADD

        """
        lines = self._setup("ADD", lines)

        for line in lines:
            values = line.split(" ")
            frompath = values.pop(0)

            # Custom parsing for frompath

            # If it's a web address, add to install routine to get
            if frompath.startswith("http"):
                for topath in values:
                    self._parse_http(frompath, topath)

            # Add the file, and decompress in install
            elif re.search("[.](gz|gzip|bz2|xz)$", frompath.strip()):
                for topath in values:
                    self._parse_archive(frompath, topath)

            # Just add the files
            else:
                for topath in values:
                    self._add_files(frompath, topath)

    # File Handling

    def _add_files(self, source, dest, layer=None):
        """add files is the underlying function called to add files to the
        list, whether originally called from the functions to parse archives,
        or https. We make sure that any local references are changed to
        actual file locations before adding to the files list.

        Parameters
        ==========
        source: the source
        dest: the destiation
        """

        # Warn the user Singularity doesn't support expansion
        if "*" in source:
            print("Singularity doesn't support expansion, * found in %s" % source)

        # Warning if file/folder (src) doesn't exist
        if not os.path.exists(source) and layer is None:
            print("%s doesn't exist, ensure exists for build" % source)

        # The pair is added to the files as a list
        if not layer:
            self.recipe[self.active_layer].files.append([source, dest])

        # Unless the file is to be copied from a particular layer
        else:
            if layer not in self.recipe[self.active_layer].layer_files:
                self.recipe[self.active_layer].layer_files[layer] = []
            self.recipe[self.active_layer].layer_files[layer].append([source, dest])

    def _parse_http(self, url, dest):
        """will get the filename of an http address, and return a statement
        to download it to some location

        Parameters
        ==========
        url: the source url to retrieve with curl
        dest: the destination folder to put it in the image

        """
        file_name = os.path.basename(url)
        download_path = "%s/%s" % (dest, file_name)
        command = "curl %s -o %s" % (url, download_path)
        self.recipe[self.active_layer].install.append(command)

    def _parse_archive(self, targz, dest):
        """parse_targz will add a line to the install script to extract a
        targz to a location, and also add it to the files.

        Parameters
        ==========
        targz: the targz to extract
        dest: the location to extract it to

        """

        # Add command to extract it
        self.recipe[self.active_layer].install.append("tar -zvf %s %s" % (targz, dest))

        # Ensure added to container files
        return self._add_files(targz, dest)

    # Comments and Default

    def _comment(self, line):
        """Simply add the line to the install as a comment. This function is
        equivalent to default, but added in the case we need future custom
        parsing (meaning a comment is different from a line.

        Parameters
        ==========
        line: the line from the recipe file to parse to INSTALL

        """
        self.recipe[self.active_layer].install.append(line)

    def _default(self, line):
        """the default action assumes a line that is either a command (a
        continuation of a previous, for example) or a comment.

        Parameters
        ==========
        line: the line from the recipe file to parse to INSTALL
        """
        if line.strip().startswith("#"):
            return self._comment(line)
        self.recipe[self.active_layer].install.append(line)

    # Ports and Volumes

    def _volume(self, line):
        """We don't have logic for volume for Singularity, so we add as
        a comment in the install, and a metadata value for the recipe
        object

        Parameters
        ==========
        line: the line from the recipe file to parse to INSTALL

        """
        volumes = self._setup("VOLUME", line)
        if volumes:
            self.recipe[self.active_layer].volumes += volumes
        return self._comment("# %s" % line)

    def _expose(self, line):
        """Again, just add to metadata, and comment in install.

        Parameters
        ==========
        line: the line from the recipe file to parse to INSTALL

        """
        ports = self._setup("EXPOSE", line)
        if ports:
            self.recipe[self.active_layer].ports += ports
        return self._comment("# %s" % line)

    def _stopsignal(self, line):
        """Again, just add to metadata, and comment in install.

        Parameters
        ==========
        line: the line from the recipe file to parse STOPSIGNAL
        """
        return self._comment("# %s" % line)

    # Working Directory

    def _workdir(self, line):
        """A Docker WORKDIR command simply implies to cd to that location

        Parameters
        ==========
        line: the line from the recipe file to parse for WORKDIR

        """
        # Save the last working directory to add to the runscript
        workdir = self._setup("WORKDIR", line)
        workdir_mkdir = "mkdir -p %s" % ("".join(workdir))
        self.recipe[self.active_layer].install.append(workdir_mkdir)
        workdir_cd = "cd %s" % ("".join(workdir))
        self.recipe[self.active_layer].install.append(workdir_cd)
        self.recipe[self.active_layer].workdir = workdir[0]

    # Entrypoint and Command

    def _cmd(self, line):
        """_cmd will parse a Dockerfile CMD command

        eg: CMD /code/run_uwsgi.sh --> /code/run_uwsgi.sh.
            If a list is provided, it's parsed to a list.

        Parameters
        ==========
        line: the line from the recipe file to parse for CMD

        """
        cmd = self._setup("CMD", line)[0]
        self.recipe[self.active_layer].cmd = self._load_list(cmd)

    def _load_list(self, line):
        """load an entrypoint or command, meaning it can be wrapped in a list
        or a regular string. We try loading as json to return an actual
        list. E.g., after _setup, we might go from 'ENTRYPOINT ["one", "two"]'
        to '["one", "two"]', and this function loads as json and returns
        ["one", "two"]
        """
        try:
            line = json.loads(line)
        except Exception:
            pass
        return line

    def _entry(self, line):
        """_entrypoint will parse a Dockerfile ENTRYPOINT command

        Parameters
        ==========
        line: the line from the recipe file to parse for CMD

        """
        entrypoint = self._setup("ENTRYPOINT", line)[0]
        self.recipe[self.active_layer].entrypoint = self._load_list(entrypoint)

    # Labels

    def _label(self, line):
        """_label will parse a Dockerfile label

        Parameters
        ==========
        line: the line from the recipe file to parse for CMD

        """
        label = self._setup("LABEL", line)
        self.recipe[self.active_layer].labels += [label]

    # Main Parsing Functions

    def _get_mapping(self, line, parser=None, previous=None):
        """mapping will take the command from a Dockerfile and return a map
        function to add it to the appropriate place. Any lines that don't
        cleanly map are assumed to be comments.

        Parameters
        ==========
        line: the list that has been parsed into parts with _split_line
        parser: the previously used parser, for context

        Returns
        =======
        function: to map a line to its command group

        """

        # Split the command into cleanly the command and rest
        if not isinstance(line, list):
            line = self._split_line(line)

        # No line we will give function to handle empty line
        if not line:
            return None

        cmd = line[0].upper()

        mapping = {
            "ADD": self._add,
            "ARG": self._arg,
            "COPY": self._copy,
            "CMD": self._cmd,
            "ENTRYPOINT": self._entry,
            "ENV": self._env,
            "EXPOSE": self._expose,
            "FROM": self._from,
            "HEALTHCHECK": self._test,
            "RUN": self._run,
            "WORKDIR": self._workdir,
            "MAINTAINER": self._label,
            "VOLUME": self._volume,
            "LABEL": self._label,
            "STOPSIGNAL": self._stopsignal,
        }

        # If it's a command line, return correct function
        if cmd in mapping:
            return mapping[cmd]

        # If it's a continued line, return previous
        cleaned = self._clean_line(line[-1])
        previous = self._clean_line(previous)

        # if we are continuing from last
        if cleaned.endswith("\\") and parser or previous.endswith("\\"):
            return parser

        return self._default

    def _clean_line(self, line):
        """clean line will remove comments, and strip the line of newlines
        or spaces.

        Parameters
        ==========
        line: the string to parse into parts

        Returns
        =======
        line: a cleaned line

        """
        # A line that is None should return empty string
        line = line or ""
        return line.split("#")[0].strip()


class SingularityWriter:
    """
    taken and modified from https://github.com/singularityhub/singularity-cli

    source of class:
    https://github.com/singularityhub/singularity-cli/blob/master/spython/main/parse/writers/base.py
    https://github.com/singularityhub/singularity-cli/blob/master/spython/main/parse/writers/singularity.py
    """

    name = "singularity"

    def __init__(self, recipe=None):
        """a writer base will take a recipe object (parser.base.Recipe) and
        provide helpers for writing to file.

        Parameters
        ==========
        recipe: the recipe instance to parse

        """
        self.recipe = recipe

    def __str__(self):
        """show the user the recipe object, along with the type. E.g.,

        [spython-writer][docker]
        [spython-writer][singularity]

        """
        base = "[spython-writer]"
        if hasattr(self, "name"):
            base = "%s[%s]" % (base, self.name)
        return base

    def __repr__(self):
        return self.__str__()

    def write(self, output_file=None, force=True):
        """convert a recipe to a specified format, and write to file, meaning
        we use the loaded recipe to write to an output file.
        If the output file is not specified, a temporary file is used.

        Parameters
        ==========
        output_file: the file to save to, not required (estimates default)
        force: if True, if file exists, over-write existing file

        """
        if output_file is None:
            output_file = self._get_conversion_outfile()

        # Cut out early if file exists and we aren't overwriting
        if os.path.exists(output_file) and not force:
            print("%s exists, and force is False." % output_file)
            sys.exit(1)

        # Do the conversion if function is provided by subclass
        if hasattr(self, "convert"):
            converted = self.convert()
            print("Saving to %s" % output_file)
            with open(output_file, "w") as filey:
                filey.writelines(converted)

    def validate(self):
        """validate that all (required) fields are included for the Docker
        recipe. We minimimally just need a FROM image, and must ensure
        it's in a valid format. If anything is missing, we exit with error.
        """
        if self.recipe is None:
            print("Please provide a Recipe() to the writer first.")
            sys.exit(1)

    def convert(self, runscript="", force=False):
        """docker2singularity will return a Singularity build recipe based on
        a the loaded recipe object. It doesn't take any arguments as the
        recipe object contains the sections, and the calling function
        determines saving / output logic.
        """
        self.validate()

        # Write single recipe that includes all layer
        recipe = []

        # Number of layers
        num_layers = len(self.recipe)
        count = 0

        # Write each layer to new file
        for stage, parser in self.recipe.items():
            # Set the first and active stage
            self.stage = stage

            # From header is required
            if parser.fromHeader is None:
                print("Singularity recipe requires a from header.")
                sys.exit(1)

            recipe += ["\n\n\nBootstrap: docker"]
            recipe += ["From: %s" % parser.fromHeader]
            recipe += ["Stage: %s\n\n\n" % stage]

            # TODO: stopped here - bug with files being found
            # Add global files, and then layer files
            recipe += self._create_section("files")
            for layer, files in parser.layer_files.items():
                recipe += self.create_keyval_section(files, "files", layer)

            # Sections with key value pairs
            recipe += self._create_section("labels")
            recipe += self._create_section("install", "post")
            recipe += self._create_section("environ", "environment")

            # If we are at the last layer, write the runscript
            if count == num_layers - 1:
                runscript = self._create_runscript(runscript, force)

                # If a working directory was used, add it as a cd
                if parser.workdir is not None:
                    runscript = ["cd " + parser.workdir] + [runscript]

                # Finish the recipe, also add as startscript
                recipe += self.finish_section(runscript, "runscript")
                recipe += self.finish_section(runscript, "startscript")

                if parser.test is not None:
                    recipe += self.finish_section(parser.test, "test")
            count += 1

        # Clean up extra white spaces
        recipe = "\n".join(recipe).replace("\n\n", "\n").strip("\n")
        return recipe.rstrip()

    def _create_runscript(self, default="", force=False):
        """create_entrypoint is intended to create a singularity runscript
        based on a Docker entrypoint or command. We first use the Docker
        ENTRYPOINT, if defined. If not, we use the CMD. If neither is found,
        we use function default.

        Parameters
        ==========
        default: set a default entrypoint, if the container does not have
                 an entrypoint or cmd.
        force: If true, use default and ignore Dockerfile settings
        """
        entrypoint = default

        # Only look at Docker if not enforcing default
        if not force:
            if self.recipe[self.stage].entrypoint is not None:
                # The provided entrypoint can be a string or a list
                if isinstance(self.recipe[self.stage].entrypoint, list):
                    entrypoint = " ".join(self.recipe[self.stage].entrypoint)
                else:
                    entrypoint = "".join(self.recipe[self.stage].entrypoint)

            if self.recipe[self.stage].cmd is not None:
                if isinstance(self.recipe[self.stage].cmd, list):
                    entrypoint = entrypoint + " " + " ".join(self.recipe[self.stage].cmd)
                else:
                    entrypoint = entrypoint + " " + "".join(self.recipe[self.stage].cmd)

        # Entrypoint should use exec
        if not entrypoint.startswith("exec"):
            entrypoint = "exec %s" % entrypoint

        # Should take input arguments into account
        if not re.search('"?[$]@"?', entrypoint):
            entrypoint = '%s "$@"' % entrypoint
        return entrypoint

    def _create_section(self, attribute, name=None, stage=None):
        """create a section based on key, value recipe pairs,
         This is used for files or label

        Parameters
        ==========
        attribute: the name of the data section, either labels or files
        name: the name to write to the recipe file (e.g., %name).
              if not defined, the attribute name is used.

        """

        # Default section name is the same as attribute
        if name is None:
            name = attribute

        # Put a space between sections
        section = ["\n"]

        # Only continue if we have the section and it's not empty
        try:
            section = getattr(self.recipe[self.stage], attribute)
        except AttributeError:
            print("Recipe does not have section for %s" % attribute)
            return section

        # if the section is empty, don't print it
        if not section:
            return section

        # Files
        if attribute in ["files", "labels"]:
            return self.create_keyval_section(section, name, stage)

        # An environment section needs exports
        if attribute in ["environ"]:
            return self.create_env_section(section, name)

        # Post, Setup
        return self.finish_section(section, name)

    def finish_section(self, section, name):
        """finish_section will add the header to a section, to finish the recipe
        take a custom command or list and return a section.

        Parameters
        ==========
        section: the section content, without a header
        name: the name of the section for the header

        """

        if not isinstance(section, list):
            section = [section]

        # Convert USER lines to change user
        lines = []
        for line in section:
            if re.search("^USER", line):
                username = line.replace("USER", "", 1).rstrip()
                line = "su - %s" % username + " # " + line
            lines.append(line)

        header = ["%" + name]
        return header + lines

    def create_keyval_section(self, pairs, name, layer):
        """create a section based on key, value recipe pairs,
         This is used for files or label

        Parameters
        ==========
        section: the list of values to return as a parsed list of lines
        name: the name of the section to write (e.g., files)
        layer: if a layer name is provided, name section
        """
        if layer:
            section = ["%" + name + " from %s" % layer]
        else:
            section = ["%" + name]
        for pair in pairs:
            section.append(" ".join(pair).strip().strip("\\"))
        return section

    def create_env_section(self, pairs, name):
        """environment key value pairs need to be joined by an equal, and
         exported at the end.

        Parameters
        ==========
        section: the list of values to return as a parsed list of lines
        name: the name of the section to write (e.g., files)

        """
        section = ["%" + name]
        for pair in pairs:
            section.append("export %s" % pair)
        return section


def convert_dockerfile_to_apptainer(in_docker_context: str, out_apptainer_file: str):
    for file in os.listdir(in_docker_context):
        if file == "Dockerfile":
            in_docker_file = remove_redundant_slashes(in_docker_context + "/" + file)
    recipeParser = DockerParser(in_docker_file)
    recipeWriter = SingularityWriter(recipeParser.recipe)
    recipeWriter.write(out_apptainer_file)


# - compose converter ------------------------------------------------------------------------------


class ParsingError(Exception):

    def __init__(self, message="parsing error"):
        super().__init__(message)


class ComposeService:

    def __init__(self):
        self.name: str = None
        self.image: str = None
        self.def_file: str = None
        self.sif_file: str = None
        self.build: str = None
        self.exec_command: list[str] = None
        self.volumes: dict[str, str] = {}
        self.environment: dict[str, str] = {}

    def command_to_list(self, args) -> list[str]:
        l = ["apptainer"]
        if args.COMMAND == "build":
            l += [
                "build",
                "-F",
                self.sif_file,
                self.def_file,
            ]
        else:
            if args.COMMAND == "up":
                if self.exec_command:
                    l.append("exec")
                else:
                    l.append("run")
            elif args.COMMAND == "run":
                l.append("run")
            if args.writable_tmpfs:
                l.append("--writable-tmpfs")
            for vol in self.volumes.values():
                l += ["--bind", vol]
            if self.environment:
                for k, v in self.environment.items():
                    l += ["--env", k + "=" + v]
            if self.build:
                l += [self.sif_file]
            elif self.image:
                l += [self.image]
            if args.COMMAND == "run":
                l += args.run_command
            elif self.exec_command:
                l += self.exec_command
        return l

    def command_to_str(self, args):
        return " ".join(self.command_to_list(args))

    def __str__(self) -> str:
        s = ""
        for k, v in self.__dict__.items():
            if v:
                s += k + ": " + str(v) + ", "
        s = "<class 'ComposeService': " + s[:-2] + ">"
        return s

    def __repr__(self) -> str:
        return str(self)


class ComposeServiceContainer:

    def __init__(self):
        self.args: Namespace = None
        self.compose_services: list[ComposeService] = []


class LineReader:

    def __init__(self, file_path):
        self.n: int = None
        self.line: str = None
        self.generator: Generator[tuple[int, str], None, None] = self.create_generator(file_path)

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
                    yield n, line
        yield n + 1, None

    def move_to_next_line(self):
        try:
            self.n, self.line = next(self.generator)
        except:
            pass

    def __str__(self) -> str:
        return f"{self.n}: {self.line}"

    def __repr__(self) -> str:
        return self.__str__()


def validate_string(s: str, additional_chars: list[str] = None) -> str:
    if additional_chars is None:
        additional_chars = []
    for invalid_char in [" ", ": "] + additional_chars:
        if invalid_char in s:
            raise ParsingError()
    return s


def get_key_and_potential_value(s: str) -> tuple[str, str]:
    key = None
    value = None
    if s[-1] == ":":
        key = validate_string(s[:-1], [":"])
    else:
        key_value_list = s.split(": ")
        if len(key_value_list) != 2:
            raise ParsingError()
        key = validate_string(key_value_list[0])
        value = key_value_list[1].lstrip()
        if value == "" or value.isspace():
            value = None
    return key, value


def remove_redundant_slashes(path):
    return path.replace("//", "/").replace("/./", "/")


def parse_volumes(lr: LineReader, cs: ComposeService):
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line[:6] == "      " and lr.line[6] == "-":
            vol = lr.line[7:].lstrip().rstrip()
            if vol.count(":") not in [1, 2]:
                raise ParsingError()
            else:
                vol = ":".join(vol.split(":")[:2])
                vol_container = vol.split(":")[1]
                cs.volumes[vol_container] = vol
        else:
            break
        lr.move_to_next_line()
    return cs


def parse_environment(lr: LineReader, cs: ComposeService):
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line[:6] == "      " and lr.line[6] != " ":
            key, value = get_key_and_potential_value(lr.line[6:])
            if value == "null":
                value = ""
            elif value[0] == '"' and value[-1] == '"':
                value = "'" + value[1:-1] + "'"
            elif value[0] != "'" and value[-1] != "'":
                value = "'" + value + "'"
            cs.environment[key] = value
        else:
            break
        lr.move_to_next_line()
    return cs


def parse_extends(lr: LineReader, cs: ComposeService):
    lr.move_to_next_line()
    parent_csc = None
    parent_service_name = None
    parent_file_location = None
    while lr.line is not None:
        if lr.line[:6] == "      " and lr.line[6] != " ":
            key, value = get_key_and_potential_value(lr.line[6:])
            if key == "file":
                parent_file_location = value
                parent_csc = state_start(LineReader(value), ComposeServiceContainer())
            elif key == "service":
                parent_service_name = value
        if lr.line[:4] == "    " and lr.line[4] != " ":
            break
        lr.move_to_next_line()
    if parent_csc is None or parent_service_name is None:
        raise ParsingError()
    parent_cs = None
    for parent_cs_potential in parent_csc.compose_services:
        if parent_cs_potential.name == parent_service_name:
            parent_cs = parent_cs_potential
    if parent_cs is None:
        raise ParsingError()
    for key, value in cs.__dict__.items():
        if value:
            parent_cs.__setattr__(key, value)
    parent_file_folder = parent_file_location.rsplit("/", 1)[0]
    if parent_cs.build:
        if parent_cs.build == ".":
            parent_cs.build = parent_file_folder
        else:
            parent_build = remove_redundant_slashes(parent_file_folder + "/" + parent_cs.build)
            parent_cs.build = parent_build
        parent_cs.def_file = remove_redundant_slashes(parent_file_folder + "/" + parent_cs.def_file)
        parent_cs.sif_file = remove_redundant_slashes(parent_file_folder + "/" + parent_cs.sif_file)
    volumes_new = {}
    for k, v in parent_cs.volumes.items():
        volumes_new[k] = remove_redundant_slashes(parent_file_folder + "/" + v)
    parent_cs.volumes = volumes_new
    return parent_cs


def state_individual_service(lr: LineReader, cs: ComposeService) -> ComposeService:
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line[:4] == "    " and lr.line[4] != " ":
            key, value = get_key_and_potential_value(lr.line[4:])
            if key == "image":
                cs.image = "docker://" + validate_string(value)
            elif key == "build":
                cs.build = validate_string(value)
                if value == ".":
                    cs.def_file = cs.name + ".def"
                    cs.sif_file = cs.name + ".sif"
            elif key == "command":
                cs.exec_command = value.split(" ")
            elif key == "volumes":
                if value is None:
                    cs = parse_volumes(lr, cs)
                continue
            elif key == "environment":
                if value is None:
                    cs = parse_environment(lr, cs)
                continue
            elif key == "extends":
                cs = parse_extends(lr, cs)
                continue
            elif key in ["networks"]:
                warnings.warn(f"'{key}' is not supported. Ignoring", UserWarning)
            else:
                raise ParsingError()
        lr.move_to_next_line()
    return cs


def state_root_services(lr: LineReader, csc: ComposeServiceContainer) -> ComposeServiceContainer:
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line[:2] == "  " and lr.line[2] != " ":
            service_name, value = get_key_and_potential_value(lr.line[2:])
            if value is not None:
                raise ParsingError()
            else:
                cs = ComposeService()
                cs.name = service_name
                cs = state_individual_service(lr, cs)
                csc.compose_services.append(cs)
        lr.move_to_next_line()
    return csc


def state_start(lr: LineReader, csc: ComposeServiceContainer) -> ComposeServiceContainer:
    lr.move_to_next_line()
    while lr.line is not None:
        if lr.line.startswith("services:"):
            state_root_services(lr, csc)
        lr.move_to_next_line()
    return csc


# - main -------------------------------------------------------------------------------------------


def parse() -> ComposeServiceContainer:
    parser = argparse.ArgumentParser(prog="apptainer_compose.py", description="Apptainer Compose")
    parser.add_argument("-f", "--file", help="file")

    subparsers = parser.add_subparsers(dest="COMMAND", required=True)

    up_parser = subparsers.add_parser("up", help="Start services")
    up_parser.add_argument("--writable-tmpfs", action="store_true", help="Enable writable tmpfs")

    subparsers.add_parser("build", help="Stop services")

    run_parser = subparsers.add_parser("run", help="Run custom command")
    run_parser.add_argument("service_name", help="Service name")
    run_parser.add_argument("run_command", nargs="*", help="Command and arguments to run")
    run_parser.add_argument("--writable-tmpfs", action="store_true", help="Enable writable tmpfs")

    args = parser.parse_args()
    if args.file is None:
        args.file = "compose.yaml"
    print(f"COMMAND: {args.COMMAND}")
    print(f"file: {args.file}")
    if args.COMMAND == "run":
        print(args.run_command)
    if args.COMMAND == "up":
        print(f"writable-tmpfs: {args.writable_tmpfs}")

    csc = ComposeServiceContainer()
    csc.args = args
    return state_start(LineReader(args.file), csc)


def execute(cmd_list: list[str]):
    result = subprocess.run(cmd_list)
    sys.exit(result.returncode)


def main():
    csc = parse()
    for cs in csc.compose_services:
        if csc.args.COMMAND == "build":
            convert_dockerfile_to_apptainer(cs.build, cs.def_file)
        print(cs.name)
        print(cs)
        print(cs.command_to_str(csc.args))
        execute(cs.command_to_list(csc.args))


if __name__ == "__main__":
    main()
