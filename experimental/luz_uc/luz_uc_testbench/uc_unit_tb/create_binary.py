PROGRAM_NAME = 'program.lasm'
HEXFILE_NAME = 'program.hex'

import sys
sys.path.insert(0, '../../../luz_asm_sim')

from lib.asmlib.assembler_driver import assemble_binary

assemble_binary([PROGRAM_NAME], output='program.hex')
