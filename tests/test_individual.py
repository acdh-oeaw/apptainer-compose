import os
import subprocess
import sys
from importlib import util
from importlib.machinery import SourceFileLoader
from pathlib import Path


apptainer_main_path = Path(__file__).resolve().parent.parent / "apptainer-compose"
spec = util.spec_from_file_location("apptainer_compose", apptainer_main_path, loader=SourceFileLoader("apptainer_compose", str(apptainer_main_path)))
apptainer_compose = util.module_from_spec(spec)
spec.loader.exec_module(apptainer_compose)


sys.argv = None
# os.chdir("./test_cases/compose_yaml/execution/services_service_environment")
os.chdir("../tmp_parsing_refactoring_test/")
sys.argv = ["../apptainer-compose", "--verbose", "up"]
apptainer_compose.main()
