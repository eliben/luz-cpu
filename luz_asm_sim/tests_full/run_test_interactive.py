# Run a single full test in interactive command-line mode.
# This is useful for debugging full tests.
#
# Eli Bendersky (C) 2008-2010
#
import os, sys
import optparse

sys.path.insert(0, '..')
from testrun_utils import link_asmfiles
from lib.commonlib.portability import printme
from lib.simlib.luzsim import LuzSim
from lib.simlib.interactive_cli import interactive_cli_sim


# Setup options
#
optparser = optparse.OptionParser(
    usage='usage: %prog [options] <testname>')
optparser.add_option('-i', '--interactive', dest='interactive',
        action='store_true', help='run interactive debugger')

optparser.set_defaults(interactive=False)

# Parse command-line arguments. 'args' should be a single test name
#
(options, args) = optparser.parse_args()

if len(args) < 1:
    optparser.print_help()
    sys.exit(1)

asmfiles = []

for file in os.listdir(os.path.join('.', args[0])):
    path = os.path.join(args[0], file)
    if os.path.splitext(path)[1] == '.lasm':
        asmfiles.append(path)

img = link_asmfiles(asmfiles)

if options.interactive:
    interactive_cli_sim(img)
else:
    sim = LuzSim(img, debug_print=True)
    sim.run()
    printme('Finished successfully...\n')
    printme('Debug queue contents:\n')
    printme(map(lambda n: '0x%X' % n, sim.debugq.items))
    



