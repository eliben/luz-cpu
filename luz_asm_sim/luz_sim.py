from lib.simlib.interactive_cli import interactive_cli_sim


if __name__ == '__main__':
    from lib.asmlib.assembler import Assembler
    from lib.asmlib.linker import Linker
    from lib.commonlib.luz_defs import (
        USER_MEMORY_START, USER_MEMORY_SIZE)
    
    code = r'''
        .segment code
        .global asm_main
    asm_main:
        addi $r5, $zero, 0x45
        halt
    '''
    
    asm = Assembler()
    objs = [asm.assemble(code)]
    link = Linker(USER_MEMORY_START, USER_MEMORY_SIZE)
    img = link.link(objs)
    
    interactive_cli_sim(img)
    