import sys
import unittest

from lib.commonlib.utils import *
from lib.commonlib.luz_opcodes import *
from lib.asmlib.asm_common_types import *

from lib.asmlib.asm_instructions import (
    InstructionError, assemble_instruction,
    register_alias, register_alias_of,
    _reg, _const, _define_or_const, _memref,
    _branch_offset,
    _instr_call, _instr_li, _instr_addi,
    _instr_lb, _instr_sh)
from lib.asmlib.asmparser import Id, Number, MemRef


class TestPrimitives(unittest.TestCase):
    def assert_instr_error(self, callable, *args, **kwargs):
        self.assertRaises(InstructionError, callable, *args, **kwargs)

    def test_signed_fits_in_nbits(self):
        self.assertTrue(num_fits_in_nbits(7, 4, signed=True))
        self.assertTrue(not num_fits_in_nbits(8, 4, signed=True))
        self.assertTrue(num_fits_in_nbits(-8, 4, signed=True))
        self.assertTrue(not num_fits_in_nbits(-9, 4, signed=True))

    def test_unsigned_fits_in_nbits(self):
        self.assertTrue(num_fits_in_nbits(15, 4))
        self.assertTrue(not num_fits_in_nbits(16, 4))
        self.assertTrue(not num_fits_in_nbits(-1, 4))

    def test_reg(self):
        self.assertEqual(_reg(Id('$r5')), 5)
        self.assertEqual(_reg(Id('$r0')), 0)
        self.assertEqual(_reg(Id('$r31')), 31)
        self.assertEqual(_reg(Id('$ra')), 31)
        self.assertEqual(_reg(Id('$zero')), 0)

        self.assert_instr_error(_reg, 5)
        self.assert_instr_error(_reg, 'r5')
        self.assert_instr_error(_reg, Id('r2'))
        self.assert_instr_error(_reg, Id('$r55'))
        self.assert_instr_error(_reg, Id('$ar5'))
        self.assert_instr_error(_reg, Id('$rx'))

    def test_const(self):
        self.assertEqual(_const(Number(13)), 13)
        self.assertEqual(_const(Number(-13)), -13)
        self.assertEqual(_const(Number(13), 4), 13)
        self.assertEqual(_const(Number(7), 3), 7)

        self.assert_instr_error(_const, 6)
        self.assert_instr_error(_const, Number(6), 2)
        self.assert_instr_error(_const, Number('woo'))
        self.assert_instr_error(_const, Number(8), 3)

    def test_define_or_const(self):
        d = {'TOM': 10, 'ff': 15}

        self.assertEqual(_define_or_const(Id('TOM'), d, 8), 10)
        self.assertEqual(_define_or_const(Id('ff'), d, 4), 15)

        d = {'TOM': 10, 'ff': 16}
        self.assert_instr_error(_define_or_const, Id('tom'), d)
        self.assert_instr_error(_define_or_const, Id('ff'), d, 4)

    def test_memref(self):
        mr = MemRef(offset=Number(val=68), id=Id('$r2'))
        self.assertEqual(_memref(mr, {}), (2, 68))

        mr = MemRef(offset=Id('JOE'), id=Id('$r2'))
        self.assertEqual(_memref(mr, {'JOE': 55}), (2, 55))

        mr = MemRef(offset=Number(val=-55), id=Id('$r22'))
        self.assertEqual(_memref(mr, {}), (22, -55))

        mr = MemRef(offset=Number(val=67000), id=Id('$r22'))
        self.assert_instr_error(_memref, mr, {})

        mr = MemRef(offset=Number(val=27000), id=Id('b2'))
        self.assert_instr_error(_memref, mr, {})

    def test_branch_offset(self):
        self.assertEqual(
            _branch_offset(Number(0x100), 16, (), ()),
            0x100)

        # offset too large
        self.assert_instr_error(_branch_offset,
            Number(0x10000), 16, (), ())

        # for 26 bits it's OK
        self.assertEqual(
            _branch_offset(Number(0x10000), 26, (), ()),
            0x10000)

        # marginal... but still OK
        self.assertEqual(
            _branch_offset(Number(-32768), 16, ('text', 0), ()),
            -32768)

        # a bit too negative...
        self.assert_instr_error(_branch_offset,
            Number(-32769), 16, (), ())

        # but OK for 17 bits
        self.assertEqual(
            _branch_offset(Number(-32769), 17, (), ()),
            -32769)

        symtab = {
            'loop': ('text', 0x200000),
            'lab':  ('text', 0x300000),
        }

        self.assertEqual(
            _branch_offset(Id('loop'), 16, ('text', 0x200600), symtab),
            -0x180)

        self.assertEqual(
            _branch_offset(Id('lab'), 16, ('text', 0x2FF720), symtab),
            0x238)

        # no such label
        self.assert_instr_error(_branch_offset,
            Id('nolab'), 16, ('text', 0x2000000), symtab)

        # label segment != instr segment
        self.assert_instr_error(_branch_offset,
            Id('lab'), 16, ('foo', 0x300100), symtab)

        # too far.
        # 0x200000 - 0x1E0000 = 0x20000 / 4 = 0x8000
        # which doesn't fit as signed into 16 bits
        #
        self.assert_instr_error(_branch_offset,
            Id('loop'), 16, ('text', 0x1E0000), symtab)

        # but this is OK
        self.assertEqual(
            _branch_offset(Id('loop'), 16, ('text', 0x1E0004), symtab),
            0x7FFF)

        # this also, because of 17 bits
        self.assertEqual(
            _branch_offset(Id('loop'), 17, ('text', 0x1E0000), symtab),
            0x8000)

    def test_register_alias(self):
        self.assertEqual(register_alias['$s6'], 24)
        self.assertEqual(register_alias_of[24], '$s6')


# Most instruction constructors are basic translation functions,
# and testing them all is too much work.
# Anyway, it will be done in the upper-level assembler tests.
#
# Here we'll test only the most complicated instructions, the
# implementation of which is non-trivial.
#
class TestInstructions(unittest.TestCase):
    def assert_instr_error(self, callable, *args, **kwargs):
        self.assertRaises(InstructionError, callable, *args, **kwargs)

    def assert_asm_instr(self, asm_instr, op, import_req=None, reloc_req=None):
        self.assertEqual(asm_instr.op, op)
        self.assertEqual(asm_instr.import_req, import_req)
        self.assertEqual(asm_instr.reloc_req, reloc_req)

    def test_immediates(self):
        ia = _instr_addi([Id('$r5'), Id('$r25'), Number(-6)], {}, {}, {})
        self.assertEqual(extract_bitfield(ia.op, 15, 0), 2**16 - 6)

    def test_load(self):
        lb = _instr_lb([Id('$r16'),
                        MemRef(offset=Number(val=-55), id=Id('$r22'))],
                        {}, {}, {})
        self.assertEqual(extract_bitfield(lb.op, 31, 26), OP_LB)
        self.assertEqual(extract_bitfield(lb.op, 25, 21), 16)
        self.assertEqual(extract_bitfield(lb.op, 20, 16), 22)
        self.assertEqual(extract_bitfield(lb.op, 15, 0), 2**16-55)

    def test_store(self):
        sh = _instr_sh([Id('$r15'),
                        MemRef(offset=Number(val=20), id=Id('$r10'))],
                        {}, {}, {})
        self.assertEqual(extract_bitfield(sh.op, 31, 26), OP_SH)
        self.assertEqual(extract_bitfield(sh.op, 25, 21), 10)
        self.assertEqual(extract_bitfield(sh.op, 20, 16), 15)
        self.assertEqual(extract_bitfield(sh.op, 15, 0), 20)


    def test_call(self):
        op = 0x1D << 26

        # simple numeric argument
        self.assert_asm_instr(
            _instr_call([Number(0x20)], {}, {}, {}),
            op | 0x20)

        # maximal size of numeric argument
        self.assert_asm_instr(
            _instr_call([Number(0x3FFFFFF)], {}, {}, {}),
            op | 0x3FFFFFF)

        # offset too large
        self.assert_instr_error(
            _instr_call, [Number(0x4000000)], {}, {}, {})

        symtab = {
            'loop': ('text', 0x2000),
            'lab':  ('text', 0x3000),
        }

        # simple defined number
        self.assert_asm_instr(
            _instr_call([Id('deflab')], {}, {}, {'deflab': 0x5F}),
            op | 0x5F)

        # import
        self.assert_asm_instr(
            _instr_call([Id('jason')], {}, symtab, {}),
            op, import_req=(ImportType.CALL, 'jason'))

        # relocation
        self.assert_asm_instr(
            _instr_call([Id('lab')], {}, symtab, {}),
            op | 0x3000 // 4, reloc_req=(RelocType.CALL, 'text'))

    def test_li(self):
        op_lui = 0x06 << 26
        op_ori = 0x2A << 26
        r4_rd = 4 << 21
        r4_rs = 4 << 16

        # simple numeric argument
        instrs = _instr_li([Id('$r4'), Number(0x26ABBA)], {}, {}, {})
        self.assert_asm_instr(instrs[0], op_lui | r4_rd | 0x26)
        self.assert_asm_instr(instrs[1],
            op_ori | r4_rd | r4_rs | 0xABBA)

        instrs = _instr_li([Id('$r4'), Number(0xD234454D)], {}, {}, {})
        self.assert_asm_instr(instrs[0], op_lui | r4_rd | 0xD234)
        self.assert_asm_instr(instrs[1],
            op_ori | r4_rd | r4_rs | 0x454D)

        instrs = _instr_li([Id('$r4'), Id('deflab')], {}, {}, {'deflab': 0xABCDEF})
        self.assert_asm_instr(instrs[0], op_lui | r4_rd | 0xAB)
        self.assert_asm_instr(instrs[1],
            op_ori | r4_rd | r4_rs | 0xCDEF)

        # offset too large
        self.assert_instr_error(
            _instr_li, [Id('$r4'), Number(0x123456780)], {}, {}, {})

        symtab = {
            'fab':  ('text', 0x2000789A),
            'boo':  ('text', 0x3000),
        }

        # import
        instrs = _instr_li([Id('$r4'), Id('ga')], {}, symtab, {})
        self.assert_asm_instr(instrs[0],
            op_lui | r4_rd,
            import_req=(ImportType.LI, 'ga'))

        self.assert_asm_instr(instrs[1],
            op_ori | r4_rd | r4_rs)

        # relocation
        instrs = _instr_li([Id('$r4'), Id('fab')], {}, symtab, {})
        self.assert_asm_instr(instrs[0],
            op_lui | r4_rd | 0x2000,
            reloc_req=(RelocType.LI, 'text'))

        self.assert_asm_instr(instrs[1],
            op_ori | r4_rd | r4_rs | 0x789A)

    def test_assemble_instruction_error(self):
        # nonexisting instruction
        self.assert_instr_error(
            assemble_instruction, 'joe', '', '', '', '')

        # wrong number of arguments
        self.assert_instr_error(
            assemble_instruction, 'add', [1, 2], '', '', '')

        # bad types of arguments
        self.assert_instr_error(
            assemble_instruction, 'add', [1, 2, 6], '', '', '')

        # Sanity test for a simple valid instruction
        self.assert_asm_instr(
            assemble_instruction(
                'add',
                [Id('$r4'), Id('$s6'), Id('$zero')],
                ('text', 0x1000), {}, {})[0],
            0x00980000)

    def test_pseudo_instructions(self):
        # LLI
        op_ori = 0x2A << 26
        r5_rd = 0x5 << 21

        self.assert_asm_instr(
            assemble_instruction(
                'lli',
                [Id('$r5'), Number(12)],
                ('text', 0x1000), {}, {})[0],
            op_ori | r5_rd | 12)

        # RET
        op_jr = 0x16 << 26
        r31_rd = 31 << 21
        r30_rd = 30 << 21

        self.assert_asm_instr(
            assemble_instruction('ret', [], (), {}, {})[0],
            op_jr | r31_rd)

    def test_eret(self):
        op_eret = 0x3E << 26
        self.assert_asm_instr(
            assemble_instruction('eret', [], (), {}, {})[0],
            op_eret)


if __name__ == '__main__':
    unittest.main()
