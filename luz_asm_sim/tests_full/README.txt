The full tests are complete Luz assembly programs that are assembled, linked, and run in the simulator, thus testing all the stages of the toolchain. Each test is a subdirectory, and can consist of any amount of .lasm files and a single _test.py file. 

To run a full test: 

* All the .lasm files in the directory are assembled and then linked into an executable image (the entry point for the user's code is the global `asm_main` symbol which must be defined by one of the source files).
* This image is loaded into the simulator and the simulator is started
* The simulator stops running when a HALT instruction has been encountered.
* At this point, the _test.py file is loaded and all the functions starting with 'test_' in it are executed. All are expected to return True. If some function returns False, it's an error in the full test.

run_full_tests.py:
    Runs all the full tests

run_test_interactive.py:
    Allows to run a single full test, either from start to finish or in an interactive mode (debugger).

