import re, sys, pprint, time
import unittest

from lib.simlib.luzsim import *
from lib.simlib.memoryunit import *
from lib.simlib.peripheral.errors import *
from lib.commonlib.utils import *

from lib.commonlib.luz_defs import (
    USER_MEMORY_START, USER_MEMORY_SIZE,
    ExceptionCause, exception_cause_code)
from lib.asmlib.assembler import *
from lib.asmlib.linker import *


class TestLuzSimBase(unittest.TestCase):
    """ A base test class for the simulator, with some common
        functionality.
    """
    def assemble_code(self, codestr, segment='code'):
        """ Assemble the code and return the segment data for
            the 'code' segment, to serve as a simple executable
            image.
        """
        asm = Assembler()
        codeobj = asm.assemble(str=codestr)
        return codeobj.seg_data[segment]


# Basic assembled instructions - not even linked with the startup
# segment. Since there's no linking: no absolute addresses are
# used and no procedure calls are made.
#
class TestLuzSim_basic(TestLuzSimBase):
    def run_code(self, codestr):
        image = self.assemble_code(codestr, 'code')
        sim = LuzSim(image)
        sim.run()
        return sim

    def test_init(self):
        ls = LuzSim([])
        self.assertEqual(ls.pc, USER_MEMORY_START)

    def test_halt(self):
        image1 = self.assemble_code(r'''
                    .segment code
                    addi $r10, $r0, 999
                    halt
                ''')
        ls = LuzSim(image1)

        # single step until halt
        ls.step()
        self.assertEqual(ls.halted, False)
        ls.step()
        self.assertEqual(ls.halted, True)

        # restart and run
        ls.restart()
        self.assertEqual(ls.halted, False)
        ls.run()
        self.assertEqual(ls.halted, True)
        self.assertEqual(ls.pc, USER_MEMORY_START + 4)

    def test_add_sub(self):
        codestr = r'''
                    .segment code
                    addi $r6, $r0, 25       # place 25 into $r6
                    addi $r4, $r0, 400      # place 500 into $r4
                    add $r8, $r6, $r4       # $r8 <- $r6 + $r4
                '''
        image = self.assemble_code(codestr)
        ls = LuzSim(image)

        # execute the first instruction
        ls.step()
        self.assertEqual(ls.reg_value(6), 25)

        # execute the next two instructions
        ls.step(); ls.step()
        self.assertEqual(ls.reg_value(8), 425)

        # now subtract from 0 to get a negative number
        ls = self.run_code(r'''
                    .segment code
                    subi $r6, $r0, 25
                    halt
                ''')
        ls.run()

        # values are stored in registers as unsigned
        self.assertEqual(ls.reg_value(6), 2**32 - 25)

    def test_multiplicaiton(self):
        # unsigned. result fits in 32 bits
        ls = self.run_code(r'''
                    .segment code
                    addi $r10, $r0, 999
                    addi $r11, $r0, 1023
                    mulu $r14, $r10, $r11
                    halt
                ''')

        self.assertEqual(ls.reg_value(14), 999*1023)
        self.assertEqual(ls.reg_value(15), 0)

        # unsigned. result does not fit in 32 bits
        ls = self.run_code(r'''
                    .segment code
                    addi $r10, $r0, 9999
                    lui $r11, 500           # r11 <- 500*65536
                    mulu $r14, $r10, $r11
                    halt
                ''')

        r11 = 500 << 16
        self.assertEqual(ls.reg_value(11), r11)

        val = r11 * 9999
        self.assertEqual(ls.reg_value(14), val & 0xFFFFFFFF)
        self.assertEqual(ls.reg_value(15), (val >> 32) & 0xFFFFFFFF)

        # signed. result fits in 32 bits
        ls = self.run_code(r'''
                    .segment code
                    addi $r10, $r0, 999
                    subi $r11, $r0, 1023        # r11 <- -1023
                    mul $r14, $r10, $r11
                    halt
                ''')

        self.assertEqual(ls.reg_value(14), 2**32 - 1023*999)
        self.assertEqual(ls.reg_value(15), 0)

        # signed. result doesn't fit in 32 bits
        ls = self.run_code(r'''
                    .segment code
                    addi $r10, $r0, 9999
                    mulu $r10, $r10, $r10       # r10 <- 9999**2
                    subi $r11, $r0, 30000       # r11 <- -30000
                    mul $r14, $r10, $r11
                    halt
                ''')

        val = ls.reg_value(15) * 2**32 + ls.reg_value(14)
        if signed_is_negative(ls.reg_value(15)):
            val = val - 2**64

        self.assertEqual(val, 9999**2 * (-30000))

    def test_li(self):
        ls = self.run_code(r'''
                    .segment code
                    li $r22, 0x456321AF
                    halt
                ''')
        self.assertEqual(ls.reg_value(22), 0x456321AF)

    def test_division(self):
        # both positive
        ls = self.run_code(r'''
                    .segment code
                    addi $r1, $r0, 58733
                    addi $r2, $r0, 104
                    divu $r6, $r1, $r2
                    halt
                ''')

        q, r = divmod(58733, 104)
        self.assertEqual(ls.reg_value(6), q)
        self.assertEqual(ls.reg_value(7), r)

        # numerator negative
        ls = self.run_code(r'''
                    .segment code
                    subi $r1, $r0, 58733
                    addi $r2, $r0, 104
                    div $r6, $r1, $r2
                    halt
                ''')

        q, r = divmod(-58733, 104)
        self.assertEqual(signed2int(ls.reg_value(6)), q)
        self.assertEqual(signed2int(ls.reg_value(7)), r)

    def test_logical(self):
        a = 0x1234ABCD
        b = 0xD234454D
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0x1234ABCD
                    li $r2, 0xD234454D

                    # now logical combinations
                    or $r3, $r2, $r1
                    not $r4, $r2
                    srli $r5, $r1, 4
                    slli $r6, $r1, 4
                    and $r7, $r1, $r2
                    nor $r8, $r1, $r2
                    xor $r9, $r1, $r2

                    lli $r10, 8
                    srl $r11, $r1, $r10
                    sll $r12, $r1, $r10
                    halt
                ''')

        self.assertEqual(ls.reg_value(3), a | b)
        self.assertEqual(ls.reg_value(4), ~b & MASK_WORD)
        self.assertEqual(ls.reg_value(5), 0x01234ABC)
        self.assertEqual(ls.reg_value(6), 0x234ABCD0)
        self.assertEqual(ls.reg_value(7), a & b)
        self.assertEqual(ls.reg_value(8), ~(a | b) & MASK_WORD)
        self.assertEqual(ls.reg_value(9), a ^ b)
        self.assertEqual(ls.reg_value(11), 0x001234AB)
        self.assertEqual(ls.reg_value(12), 0x34ABCD00)

    def test_branches(self):
        # unconditional branch forward
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0x1234ABCD
                    b 2
                    lli $r1, 0x0000 # skipped over
                    halt
                ''')
        self.assertEqual(ls.reg_value(1), 0x1234ABCD)

        # branch forward and then back
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0x1234ABCD
                    b 4              #--*
                    lui $r1, 0x5566  #  | <-*
                    halt             #  |   |
                    nop              #  |   |
                    lli $r1, 0x0000  #<-*   |
                    b -4             #------*
                    halt
                ''')
        self.assertEqual(ls.reg_value(1), 0x55660000)

        # equality comparison taken
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0x1234ABCD
                    li $r2, 0x1234ABCD
                    beq $r1, $r2, 2
                    lli $r1, 0  # skipped over
                    halt
                ''')
        self.assertEqual(ls.reg_value(1), 0x1234ABCD)

        # equality comparison not taken
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0x1234ABCD
                    li $r2, 0x1234ABCE  # D != E
                    beq $r1, $r2, 2
                    lli $r1, 0  # executed
                    halt
                ''')
        self.assertEqual(ls.reg_value(1), 0)

        # unsigned comparison (taken)
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0xFFFFFFFE  # as unsigned: big number
                    li $r2, 0x00000020
                    bgtu $r1, $r2, 2
                    lli $r1, 0  # skipped over
                    halt
                ''')
        self.assertEqual(ls.reg_value(1), 0xFFFFFFFE)

        # unsigned comparison (taken)
        ls = self.run_code(r'''
                    .segment code
                    li $r1, 0xFFFFFFFE  # as signed: -2
                    li $r2, 0x00000020
                    bgt $r1, $r2, 2
                    lli $r1, 0  # executed
                    halt
                ''')
        self.assertEqual(ls.reg_value(1), 0)

    def test_load(self):
        # How do we test loads/stores without a linker?
        # We know the program is placed at USER_MEMORY_START, so
        # we use this with an offset to access data in the code
        # segment.
        #
        ls = self.run_code(r'''
                    .segment code
                    li $r20, %s         # r20 points to this segment
                    lb $r4, 28($r20)    # data[0]
                    lb $r5, 29($r20)    # data[1] (sign extend)
                    lb $r6, 30($r20)    # data[2]
                    lbu $r7, 31($r20)    # data[3] (zero extend)
                    halt
                    .byte 0x45, 0xFA, 0x67, 0x99
                    ''' % USER_MEMORY_START)

        self.assertEqual(ls.reg_value(4), 0x45)
        self.assertEqual(ls.reg_value(5), 2**32-(2**8-0xFA))
        self.assertEqual(ls.reg_value(6), 0x67)
        self.assertEqual(ls.reg_value(7), 0x99)

        # test load halfwords and load word
        ls = self.run_code(r'''
                    .segment code
                    b 1                 # branch over next word
                    .byte 0x73, 0xA0, 0x45, 0x33
                    li $r20, %s         # r20 points to this segment
                    lh $r4, 4($r20)     # data[1:0] (sign extend)
                    lhu $r5, 4($r20)    # data[1:0] (zero extend)
                    lh $r6, 6($r20)     # data[3:2]
                    lw $r7, 4($r20)     # data[3:0]
                    halt
                    ''' % USER_MEMORY_START)

        self.assertEqual(ls.reg_value(4), 2**32-(2**16-0xA073))
        self.assertEqual(ls.reg_value(5), 0xA073)
        self.assertEqual(ls.reg_value(6), 0x3345)
        self.assertEqual(ls.reg_value(7), 0x3345A073)

    def test_store(self):
        ls = self.run_code(r'''
                    .segment code
                    b 2
                    .word 0
                    li $r20, %s         # r20 points to this segment
                    li $r10, 0xABCDEF12
                    sw $r10, 4($r20)
                    halt
            ''' % USER_MEMORY_START)

        self.assertEqual(ls.memory.read_mem(USER_MEMORY_START + 4, 4),
            0xABCDEF12)

        ls = self.run_code(r'''
                    .segment code
                    b 2                 # branch over next words
                    .byte 0x73, 0xA0, 0x45, 0x33
                    .word 0
                    li $r20, %s         # r20 points to this segment
                    li $r3, 0xFEDA0275
                    sw $r3, 4($r20)
                    lw $r10, 4($r20)    # r10 <- whole word
                    sh $r3, 10($r20)
                    lw $r11, 8($r20)    #
                    sb $r3, 9($r20)
                    lw $r12, 8($r20)    #
                    halt
                    ''' % USER_MEMORY_START)

        self.assertEqual(ls.reg_value(10), 0xFEDA0275)
        self.assertEqual(ls.reg_value(11), 0x02750000)
        self.assertEqual(ls.reg_value(12), 0x02757500)

    def test_loop(self):
        img = self.assemble_code(r'''
                    .segment code
                    move $r4, $zero         # r4 <- 0
                    addi $r5, $zero, 1000   # r5 <- 1000

                    # loop
                    add $r4, $r4, $r5       # r4 += r5
                    subi $r5, $r5, 1        # r5--
                    bnez $r5, -2            # loop back

                    halt
                    ''', 'code')
        ls = LuzSim(img)

        t1 = time.time()
        ls.run()
        #~ print 'elapsed', time.time() - t1

        self.assertEqual(ls.reg_value(4), 500500)


class TestLuzSim_exceptions(TestLuzSimBase):
    def assemble_code(self, codestr, segment='code'):
        asm = Assembler()
        codeobj = asm.assemble(str=codestr)
        return codeobj.seg_data[segment]

    def test_zero_div(self):
        img = self.assemble_code(r'''
                    .segment code
                    nop
                    div $r5, $r4, $r0 # div by 0 exception
                    nop
                    halt
                    ''', 'code')

        ls = LuzSim(img)
        ls.step()
        ls.step() # hits exception

        # The value stored in the exception vector is 0 by default
        self.assertEqual(ls.in_exception, True)
        self.assertEqual(ls.pc, 0)
        self.assertEqual(ls.cregs.exception_cause.value,
            exception_cause_code[ExceptionCause.DIVIDE_BY_ZERO])

    def test_memoryaccess(self):
        #
        # Exception on accessing an invalid memory address
        #
        img = self.assemble_code(r'''
                    .segment code
                    li $r8, 0x77777700
                    lw $r5, 0($r8)  # memory error exception
                    nop
                    halt
                    ''', 'code')

        ls = LuzSim(img)
        ls.step()
        ls.step() # 'li' is 2 instructions
        ls.step() # hits exception

        self.assertEqual(ls.in_exception, True)
        self.assertEqual(ls.pc, 0)
        self.assertEqual(ls.cregs.exception_cause.value,
            exception_cause_code[ExceptionCause.MEMORY_ACCESS])

        #
        # Exception on misaligned memory access
        #
        img = self.assemble_code(r'''
                    .segment code
                    li $r8, 0x100007
                    lw $r5, 0($r8)  # memory error exception
                    nop
                    halt
                    ''', 'code')

        ls = LuzSim(img)
        ls.step()
        ls.step() # 'li' is 2 instructions
        ls.step() # hits exception

        self.assert_(ls.in_exception)
        self.assertEqual(ls.pc, 0)
        self.assertEqual(ls.cregs.exception_cause.value,
            exception_cause_code[ExceptionCause.MEMORY_ACCESS])

    def test_invalid_opcode(self):
        # 0x30 is an invalid opcode
        inv = word2bytes(0x30 << 26)
        img = list(inv) + [0, 0, 0, 0]
        ls = LuzSim(img)
        ls.step()
        self.assert_(ls.in_exception)
        self.assertEqual(ls.pc, 0)
        self.assertEqual(ls.cregs.exception_cause.value,
            exception_cause_code[ExceptionCause.INVALID_OPCODE])

    def test_exception_vector_jump(self):
        img = self.assemble_code(r'''
                    .segment code
                    b 3             # skip over to main code

                    # Exception handler
                    #
                    addi $r22, $zero, 0x89
                    eret

                    # Main code
                    #
                    li $r3, %s       # place vector pointer in r3
                    sw $r3, 4($zero) # store $r3 into 0x004
                    nop
                    lw $r5, 7($zero) # align exception
                    b 0              # endless loop
                    halt
                    ''' % (USER_MEMORY_START + 4,), 'code')

        ls = LuzSim(img)
        ls.step()               # initial jump
        ls.step(); ls.step()    # li
        ls.step(); ls.step()    # sw, nop
        ls.step()               # here an exception happens

        self.assert_(ls.in_exception)
        # PC points correctly
        self.assertEqual(ls.pc, USER_MEMORY_START + 4)
        # return address from exception points correctly
        self.assertEqual(ls.cregs.exception_return_addr.value,
            USER_MEMORY_START + 0x20)

        # execute exception vector code: addi and eret
        ls.step(); ls.step();

        # out of exception, and the pc is correct
        self.assert_(not ls.in_exception)
        self.assertEqual(ls.pc, USER_MEMORY_START + 0x20)

        # and the register addition in the vector code did run
        self.assertEqual(ls.reg_value(22), 0x89)

    def test_exception_in_exception(self):
        img = self.assemble_code(r'''
                    .segment code
                    b 3             # skip over to main code

                    # Exception handler
                    #
                    lw $r6, 7($zero) # align exception
                    eret

                    # Main code
                    #
                    li $r3, %s       # place vector pointer in r3
                    sw $r3, 4($zero) # store $r3 into 0x004
                    nop
                    lw $r5, 7($zero) # align exception
                    b 0              # endless loop
                    halt
                    ''' % (USER_MEMORY_START + 4,), 'code')

        ls = LuzSim(img)
        ls.step()               # initial jump
        ls.step(); ls.step()    # li
        ls.step(); ls.step()    # sw, nop
        ls.step()               # here an exception happens

        self.assert_(ls.in_exception)
        # PC points correctly
        self.assertEqual(ls.pc, USER_MEMORY_START + 4)

        # execute the 'lw' that causes another exception
        ls.step()

        # the CPU halts
        self.assert_(ls.halted)


class TestMemoryUnit(TestLuzSimBase):
    def setUp(self):
        image = [10, 20, 30, 40, 80, 20, 50, 60]
        self.cregs = CoreRegisters()
        self.mem = MemoryUnit(image)
        self.mem.register_peripheral_map(0, 0xFFF, self.cregs)

    def test_read_cregs(self):
        self.cregs.control_1.value = 0xABBACADE
        self.assertEqual(self.mem.read_mem(0x100, 4), 0xABBACADE)

    def test_read_mem(self):
        wval0 = 40 << 24 | 30 << 16 | 20 << 8 | 10
        wval1 = 60 << 24 | 50 << 16 | 20 << 8 | 80

        hwval0 = 20 << 8 | 10
        hwval1 = 40 << 8 | 30

        self.assertEqual(wval0,
            self.mem.read_mem(USER_MEMORY_START, 4))
        self.assertEqual(wval1,
            self.mem.read_mem(USER_MEMORY_START + 4, 4))
        self.assertEqual(hwval0,
            self.mem.read_mem(USER_MEMORY_START, 2))
        self.assertEqual(hwval1,
            self.mem.read_mem(USER_MEMORY_START + 2, 2))
        self.assertEqual(50,
            self.mem.read_mem(USER_MEMORY_START + 6, 1))

    def test_read_mem_errors(self):
        self.assertRaises(MemoryAlignError,
            self.mem.read_mem, USER_MEMORY_START + 1, 4)
        self.assertRaises(MemoryAlignError,
            self.mem.read_mem, USER_MEMORY_START + 1, 2)

        self.assertRaises(MemoryAccessError,
            self.mem.read_mem, 0x55550, 4)
        self.assertRaises(PeripheralMemoryAlignError,
            self.mem.read_mem, 0, 1)
        # just a bit overboard
        self.assertRaises(MemoryAccessError,
            self.mem.read_mem,
            USER_MEMORY_START + USER_MEMORY_SIZE, 4)

    def test_write_creg(self):
        # write into writable creg
        self.mem.write_mem(0x120, 4, 0xFA)
        self.assertEqual(self.mem.read_mem(0x120, 4), 0xFA)

        # write into non-writable creg, makes no difference
        self.mem.write_mem(0x108, 4, 0xABBA)
        self.assertEqual(self.mem.read_mem(0x108, 4), 0)

    def test_write_mem(self):
        word_addr = USER_MEMORY_START + 0x20000
        # init a memory word to a known value
        self.mem.write_mem(word_addr, 4, 0xABCD1234)

        # now modify byte #2
        self.mem.write_mem(word_addr + 2, 1, 0x78)

        # make sure all other parts of the word are as before
        self.assertEqual(self.mem.read_mem(word_addr, 2), 0x1234)
        self.assertEqual(self.mem.read_mem(word_addr+3, 1), 0xAB)
        self.assertEqual(self.mem.read_mem(word_addr, 4), 0xAB781234)

    def test_write_mem_errors(self):
        self.assertRaises(MemoryAlignError,
            self.mem.write_mem, USER_MEMORY_START + 21, 4, 6)
        self.assertRaises(MemoryAlignError,
            self.mem.write_mem, USER_MEMORY_START + 21, 2, 6)


class TestPeripherals(TestLuzSimBase):
    def test_debugqueue(self):
        # Write to the DebugQueue peripheral
        #
        img = self.assemble_code(r'''
                    .segment code
                    .define ADDR_DEBUG_QUEUE, 0xF0000

                    li $s2, ADDR_DEBUG_QUEUE
                    ori $s3, $s3, 0xABBA
                    sw $s3, 0($s2)

                    halt
                    ''')

        ls = LuzSim(img)
        ls.run()

        self.assertEqual(ls.debugq.items, [0xABBA])

        # Now write to it in a loop
        #
        img = self.assemble_code(r'''
                    .segment code
                    .define ADDR_DEBUG_QUEUE, 0xF0000

                    li $r22, ADDR_DEBUG_QUEUE

                    move $r4, $zero         # r4 <- 0
                    addi $r5, $zero, 10     # r5 <- 10

                    # loop
                    sw $r5, 0($r22)
                    add $r4, $r4, $r5       # r4 += r5
                    subi $r5, $r5, 1        # r5--
                    bnez $r5, -3            # loop back

                    halt
                    ''')

        ls = LuzSim(img)
        ls.run()

        self.assertEqual(ls.debugq.items, list(range(10, 0, -1)))


if __name__ == '__main__':
    unittest.main()
