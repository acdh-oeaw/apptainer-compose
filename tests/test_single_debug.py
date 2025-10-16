from test_all_commands import main_test


tests_target_list = [("valid_up_and_build", "apptainer run valid_up_and_build.sif")]


main_test(tests_target_list)
