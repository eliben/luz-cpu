# Luz assembly driver: assembles and links a group of .lasm
# files and creates an executable image from them.
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
from optparse import OptionParser
import glob, operator

from lib.asmlib.assembler_driver import assemble_binary
from lib.commonlib.portability import printme


def run(cmdline_args):
    optparser = OptionParser()
    optparser.add_option('-o', '--output',
        dest='output',
        action='store',
        help='output file name')
    optparser.add_option('--ulba',
        dest='ulba',
        action='store',
        default='default',
        help='Upper Linear Base Address for output HEX file')
    
    if len(cmdline_args) == 0:
        optparser.print_help()
        return
    
    options, args = optparser.parse_args(cmdline_args)    
    out_filename = options.output or 'image.hex'    
    in_filenames = reduce(operator.add, [glob.glob(pat) for pat in args], [])
    
    if options.ulba == 'default':
        ulba = 0
    else:
        ulba = int(options.ulba, 16)
    
    assemble_binary(in_filenames, out_filename, ulba)
    
    printme('Created output file: %s...' % out_filename)


if __name__ == '__main__':
    import sys
    run(sys.argv[1:])




