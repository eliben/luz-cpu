import os, sys, unittest
sys.path.insert(0, '..')

from lib.asmlib.disassembler import *
from lib.commonlib.utils import *
from lib.commonlib.luz_opcodes import *


class TestDisassembler(unittest.TestCase):
    def assertDisassemble(self, op, str, replace_alias=False):
        self.assertEqual(disassemble(op, replace_alias), str)

    def test_3reg(self):
        op = (  build_bitfield(31, 26, OP_ADD) |
                build_bitfield(25, 21, 5) |
                build_bitfield(20, 16, 8) |
                build_bitfield(15, 11, 31))
        self.assertDisassemble(op, 'add $r5, $r8, $r31')
        self.assertDisassemble(op, 'add $a1, $t0, $ra', True)

    def test_2reg_imm(self):
        op = (  build_bitfield(31, 26, OP_SUBI) |
                build_bitfield(25, 21, 19) |
                build_bitfield(20, 16, 0) |
                build_bitfield(15, 0, 0xFAB0))
        self.assertDisassemble(op, 'subi $r19, $r0, 0xFAB0')
        self.assertDisassemble(op, 'subi $s1, $zero, 0xFAB0', True)

    def test_1reg_imm(self):
        op = (  build_bitfield(31, 26, OP_LUI) |
                build_bitfield(25, 21, 2) |
                build_bitfield(15, 0, 0xDEED))
        self.assertDisassemble(op, 'lui $r2, 0xDEED')

    def test_load(self):
        op = (  build_bitfield(31, 26, OP_LB) |
                build_bitfield(25, 21, 2) |
                build_bitfield(20, 16, 22) |
                build_bitfield(15, 0, 0x0020))
        self.assertDisassemble(op, 'lb $r2, 32($r22)')

        op = (  build_bitfield(31, 26, OP_LB) |
                build_bitfield(25, 21, 2) |
                build_bitfield(20, 16, 22) |
                build_bitfield(15, 0, 0xFFA0))
        self.assertDisassemble(op, 'lb $r2, -96($r22)')

    def test_store(self):
        op = (  build_bitfield(31, 26, OP_SW) |
                build_bitfield(25, 21, 2) |
                build_bitfield(20, 16, 22) |
                build_bitfield(15, 0, 0x0020))
        self.assertDisassemble(op, 'sw $r22, 32($r2)')

    def test_call(self):
        op = (  build_bitfield(31, 26, OP_CALL) |
                build_bitfield(25, 0, 0xFAD000))
        self.assertDisassemble(op, 'call 0xFAD000 [0x3EB4000]')

    def test_branch(self):
        op = (  build_bitfield(31, 26, OP_BLTU) |
                build_bitfield(25, 21, 2) |
                build_bitfield(20, 16, 22) |
                build_bitfield(15, 0, 0x0020))
        self.assertDisassemble(op, 'bltu $r2, $r22, 32')


#-----------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
