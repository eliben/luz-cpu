# Runner of full tests of the Luz assembler, linker & simulator.
# Full tests consist of a directory with some .lasm files and
# a single _test.py file
# The .lasm files are assembled, linked and simulated. When the
# simulation finishes (on CPU halt), the Python test functions in
# _test.py are executed with the simulator object to check
# expected results.
#
# Eli Bendersky (C) 2008-2010
import sys, os, time

from lib.simlib.luzsim import LuzSim
from lib.commonlib.utils import extract_bitfield
from lib.commonlib.portability import printme

from testrun_utils import get_test_functions, link_asmfiles

class FullTestError(RuntimeError): pass


def run_test_dir(dirpath):
    """ Runs a single full test, given its directory path
    """
    testfile = None
    asmfiles = []

    for file in os.listdir(dirpath):
        path = os.path.join(dirpath, file)

        if file == '_test.py':
            testfile = path
        elif os.path.splitext(path)[1] == '.lasm':
            asmfiles.append(path)

    if not asmfiles:
        return 'Empty'

    img = link_asmfiles(asmfiles)

    # Simulate
    sim = LuzSim(img)
    sim.run()

    # Run all the test functions for this test and make sure
    # they pass
    for testfunc in get_test_functions(testfile):
        if not testfunc(sim):
            raise FullTestError('failed %s in %s' % (
                    testfunc.__name__, dirpath))
    return 'OK'


def run_all(startdir='.'):
    t1 = time.time()
    for dir in os.listdir(startdir):
        if not os.path.isdir(dir):
            continue
        if not dir.startswith(('.svn', '__')):
            subdir = os.path.join(startdir, dir)
            try:
                printme('Test %s...' % subdir)
                status = run_test_dir(subdir)
                printme(status + '\n')
            except Exception:
                printme('Caught exception for dir: %s\n' % subdir)
                raise

    printme('------------------------------------------------------\n')
    printme('Elapsed: %.3fs\n' % (time.time() - t1))


#-----------------------------------------------------------------
if __name__ == '__main__':
    startdir = '.'
    if len(sys.argv) > 1:
        startdir = sys.argv[1]
    run_all(startdir)
