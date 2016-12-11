import re, sys, pprint, time

import setup_path
from lib.simlib.luzsim import *
from lib.simlib.memoryunit import *
from lib.asmlib.assembler import *



def assemble_code(codestr, segment='code'):
    asm = Assembler()
    codeobj = asm.assemble(str=codestr)
    return codeobj.seg_data[segment]


if __name__ == '__main__': 
    code = r'''
                .segment code
                li $r8, 0x77777777
                lw $r5, 0($r8)  # memory error exception
                nop
                halt
        '''
    
    asm = Assembler()
    codeobj = asm.assemble(str=code)
    print codeobj
    
    import cPickle as pickle
    d = pickle.dumps(codeobj, 2)

    print type(pickle.loads(d))

    img = assemble_code(code, 'code')

    #~ ls = LuzSim(img)
    #~ ls.step()
    #~ ls.step()
    #~ ls.step() # hits exception
    #~ print ls.in_exception
    #~ print hex(ls.pc)
    #~ print hex(ls.reg_value(8))
    #~ print hex(ls.reg_value(5))


