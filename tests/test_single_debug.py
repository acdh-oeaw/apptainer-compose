from test_all_commands import main_test


tests_target_list = [
    (
        "valid_build",
        [
            "apptainer build -F valid_build.sif valid_build.def",
            "apptainer run valid_build.sif",
        ],
    ),
]


main_test(tests_target_list)
