import re, sys, pprint
import unittest

import setup_path
from lib.asmlib.assembler import *
from lib.asmlib.asm_common_types import *
from lib.asmlib.asmparser import *
from lib.commonlib.utils import unpack_word, bytes2word, unpack_bytes


class TestAssembler(unittest.TestCase):
    """ It's quite hard to do extensive tests on this level, 
        because we have to get deep into the implementation 
        details.
        
        Therefore, these tests try to sample the "sanity checks"
        of assembly. The real "heavy" testing is done by running
        assembled code on the simulator and watching for expected
        results.
    """
    def setUp(self):
        self.asm = Assembler()

    def assemble(self, txt):
        return self.asm.assemble(txt)

    # Digs into the guts of Assembler to pull the symbol table
    # created by the first pass.
    #
    # Since this test module is developed in sync with Assembler,
    # this makes sense for more scrupulous inspection.
    #
    def symtab(self, txt):
        symtab, addr_imf = self.asm._compute_addresses(self.asm._parse(txt))
        return symtab

    def addr_imf(self, txt):
        symtab, addr_imf = self.asm._compute_addresses(self.asm._parse(txt))
        return addr_imf

    def test_firstpass_symbol_table(self):
        txt1 = r'''
                    .segment text
            lab1:   add $r1, $r2, $v1
            lab2:   add $r2, $r3, $r4
        '''
        
        # note: SegAddr are namedtuples, so they can be just 
        # compared with normal tuples
        #
        self.assertEqual(self.symtab(txt1),
            {   'lab1': ('text', 0),
                'lab2': ('text', 4)})

        txt2 = r'''
                    .segment text
            lab1:   add $r1, $r2, $r3
                    .word 1, 2, 3, 4, 5
            lab2:   add $r2, $r3, $r4
                    .alloc 50
            gaga:
        '''
        self.assertEqual(self.symtab(txt2),
            {   'lab1': ('text', 0),
                'lab2': ('text', 24),
                'gaga': ('text', 80)})

        txt3 = r'''
                    .segment text
            lab1:   add $r1, $r2, $r3
                    .byte 1, 2, 3, 4, 5
            lab2:   add $r2, $r3, $r4
                    add $r2, $r3, $r4
                    .byte 0xFF
            joe:    nop
                    nop
            kwa:    nop
                    .string "hello"
            jay:    nop
        '''
        self.assertEqual(self.symtab(txt3),
            {   'lab1': ('text', 0),
                'lab2': ('text', 12),
                'joe': ('text', 24),
                'kwa': ('text', 32),
                'jay': ('text', 44),})

        txt4 = r'''
                    .segment text
                    add $r1, $r2, $r3
            lab1:   .byte 1, 2, 4, 6, 7, 8
            lab2:   add $r1, $r2, $r3
                    .segment data
            lab3:   add $r1, $r2, $r3
            lab4: 
            lab5:   add $r1, $r2, $r3
        '''
        self.assertEqual(self.symtab(txt4),
            {   'lab1': ('text', 4),
                'lab2': ('text', 12),
                'lab3': ('data', 0),
                'lab4': ('data', 4),
                'lab5': ('data', 4)})

        txt5 = r'''
                    .segment data
            ko:     add $r4, $r4, 23
            dddd:
            br:     .string "h\n\\\"ello"
        '''
        
        self.assertEqual(self.symtab(txt5),
            {   'ko':   ('data', 0),
                'dddd': ('data', 4),
                'br':   ('data', 4)})

        # here that 0-termination of a string is taken into 
        # account.
        #
        txt51 = r'''
                    .segment text
            pow:    .string "abcd"
            jack:   nop
        '''
        self.assertEqual(self.symtab(txt51),
            {   'pow':  ('text', 0),
                'jack': ('text', 8)})
                
        txt6 = r'''
                    .segment wow
                    add $r0, $r0, $zero
                    call 12
                    li $r6, 0x45678919
                bt: nop
        '''
        
        self.assertEqual(self.symtab(txt6),
            {'bt': ('wow', 16)})

    def test_firstpass_addr_imf(self):
        txt11 = r'''
                    .segment wow
                    add $r0, $r0, $r0
                    call 12
                    li $r6, 0x45678919
                bt: nop
        '''
        aimf = self.addr_imf(txt11)
        
        self.assertEqual(aimf[0][0], ('wow', 0))
        self.assertEqual(type(aimf[0][1]), Instruction)
        self.assertEqual(aimf[3][0], ('wow', 16))
        self.assertEqual(type(aimf[3][1]), Instruction)
        
        txt12 = r'''
                    .segment text
                    add $r1, $r2, $r3
            lab1:   .byte 1, 2, 4, 6, 7, 8
            lab2:   add $r1, $r2, $r3
                    .segment data
            lab3:   add $r1, $r2, $r3
            lab4: 
            lab5:   add $r1, $r2, $r3
        '''
        aimf = self.addr_imf(txt12)
        self.assertEqual(aimf[1][0], ('text', 4))
        self.assertEqual(type(aimf[1][1]), Directive)
        self.assertEqual(aimf[4][0], ('data', 4))
        self.assertEqual(type(aimf[4][1]), Instruction)

    def test_assemble_basic_export_and_segment(self):
        txt = r'''
                    .segment text
                    .global jj
                    .global nb
                    and $r2, $r0, $r2      # clear r2
            jj:     lw $r17, 20($v1)
                
                    .segment data
                    .byte 0x14, 0x18, 0x01, 8, 9
            nb:     .word 0x56899001
            '''
        obj = self.assemble(txt)
        
        # export table
        self.assertEqual(obj.export_table[0], 
            ('jj', ('text', 4)))
        self.assertEqual(obj.export_table[1], 
            ('nb', ('data', 8)))

        # import and reloc tables should be empty
        self.assertEqual(obj.import_table, [])
        self.assertEqual(obj.reloc_table, [])
        
        self.assertEqual(len(obj.seg_data), 2)
        
        text_seg = obj.seg_data['text']
        data_seg = obj.seg_data['data']
        
        # check the correct encoding of instructions in the text
        # segment
        #
        self.assertEqual(bytes2word(text_seg[0:4]),
            9 << 26 | 2 << 21 | 2 << 11) 
        self.assertEqual(bytes2word(text_seg[4:8]),
            0xF << 26 | 17 << 21 | 3 << 16 | 20) 
        
        # check the correct placement of data in the data segment
        #
        self.assertEqual(data_seg[0:5], list(unpack_bytes(b'\x14\x18\x01\x08\x09')))
        self.assertEqual(data_seg[8:12], list(unpack_bytes(b'\x01\x90\x89\x56')))

    def test_assemble_memref_define(self):
        txt = r'''
                    .segment text 
                    .define DEF, 0x20
                    
                    lw $r3, DEF($r4)
            '''
        obj = self.assemble(txt)
        text_seg = obj.seg_data['text']
        
        self.assertEqual(bytes2word(text_seg[0:4]),
            0xF << 26 | 3 << 21 | 4 << 16 | 0x20)

    def test_assemble_basic_import(self):
        txt = r'''
                    .segment text
                    call georgia
                    jr $r29
                    li $r11, california
                    
                    .alloc 256
                    
                    call california
                    sw $r5, 0($r5)
            '''
        obj = self.assemble(txt)
        
        # export and reloc tables should be empty
        self.assertEqual(obj.export_table, [])
        self.assertEqual(obj.reloc_table, [])
        
        # import table
        self.assertEqual(obj.import_table[0], 
            ('georgia', ImportType.CALL, ('text', 0)))
        self.assertEqual(obj.import_table[1], 
            ('california', ImportType.LI, ('text', 8)))
        self.assertEqual(obj.import_table[2], 
            ('california', ImportType.CALL, ('text', 16 + 256)))
            
        # see what was actually assembled into the first CALL
        # since the constant is imported, 0 is placed in the 
        # off26 field 
        #
        text_seg = obj.seg_data['text']
        self.assertEqual(bytes2word(text_seg[0:4]),
            0x1D << 26)

    def test_assemble_basic_reloc(self):
        txt = r'''
                    .segment text
            rip1:   nop
                    call rip1
                    jr $r29
                    li $r11, rip2
                    
                    .alloc 256
                    
                    call rip3
                    sw $r5, 0($r5)
            
            rip2:   nop
            rip3:   nop
            
            '''
        obj = self.assemble(txt)
        
        # export and import tables should be empty
        self.assertEqual(obj.export_table, [])
        self.assertEqual(obj.import_table, [])
        
        # reloc table
        self.assertEqual(obj.reloc_table[0], 
            ('text', RelocType.CALL, ('text', 4)))
        self.assertEqual(obj.reloc_table[1], 
            ('text', RelocType.LI, ('text', 12)))
        self.assertEqual(obj.reloc_table[2], 
            ('text', RelocType.CALL, ('text', 276)))
        
        # make sure that the assembled instructions are correct.
        #
        text_seg = obj.seg_data['text']
        
        # the first part of LI is the LUI, which gets nothing from
        # the offset, since it's too small
        # the second part is the ORI, which gets the offset in its
        # constant field
        #
        self.assertEqual(bytes2word(text_seg[12:16]),
            0x6 << 26 | 11 << 21)
        self.assertEqual(bytes2word(text_seg[16:20]),
            0x2A << 26 | 11 << 21 | 11 << 16 | 284)

        # check call's instruction too
        self.assertEqual(bytes2word(text_seg[276:280]),
            0x1D << 26 | (288 // 4))


class TestAssemblerErrors(unittest.TestCase):
    def setUp(self):
        self.asm = Assembler()

    def assemble(self, txt):
        return self.asm.assemble(txt)

    def assert_str_contains(self, str, what):
        self.failUnless(str.find(what) > -1, '"%s" contains "%s"' % (str, what))

    def assert_error_at_line(self, msg, lineno):
        self.assert_str_contains(msg, 'lineno %s' % lineno)

    def assert_assembly_error(self, txt, msg=None, lineno=None):
        try:
            self.assemble(txt)
        except AssemblyError:
            err = sys.exc_info()[1]
            err_msg = str(err)
            
            if msg:
                self.assert_str_contains(err_msg, msg)
            
            if lineno:
                self.assert_str_contains(err_msg, 'line %s' % lineno)
        else:
            self.fail('AssemblyError not raised')

    def test_label_duplicate_error(self):
        msg = 'duplicated'
        
        txt = r'''
                    .segment text
            lbl:    add $r1, $r2, $r3
            lbl:    add $r2, $r5, $r4
        '''
        self.assert_assembly_error(txt, msg, 4)
        
        txt = r'''
                    .segment text
            lbl:    add $r1, $r2, $r3
            lab_5:  .alloc 4
            lbl6:   add $r2, $r5, $r4
                    .segment data
            lab_4:  .word 0x56664412
            lab_5:  add $r0, $r0, $r0
        '''
        self.assert_assembly_error(txt, msg, 8)        

    def test_unknown_instruction_error(self):
        txt = r'''  .segment text
                    jafa $r1, $r1, $r2
        '''
        self.assert_assembly_error(txt, 'unknown instruction', 2)
        
        txt = r'''  .segment text
                    bnez r12, lab
            lab:    jafa $r1, $r1, $r2
        '''
        self.assert_assembly_error(txt, 'unknown instruction', 3)        

    def test_segment_directive_error(self):
        seg_msg = 'segment must be defined before'
        
        txt = r'''add $r4, $r4, 2'''
        self.assert_assembly_error(txt, seg_msg, 1) 

        txt = r'''bla: .segment joe'''
        self.assert_assembly_error(txt, seg_msg, 1)
        
        txt = r'''.alloc 4'''
        self.assert_assembly_error(txt, seg_msg, 1)
    
        seg_arg_msg = 'argument(s) expected'
        txt = '.segment'
        self.assert_assembly_error(txt, seg_arg_msg, 1)
        
        txt = '.segment a, b'
        self.assert_assembly_error(txt, seg_arg_msg, 1)
        
        txt = '.segment 456'
        self.assert_assembly_error(txt, 'unexpected type', 1)
    
    def test_define_directive_error(self):
        txt = r'''
                .segment text
                .define joe, moe
            '''
        self.assert_assembly_error(txt, 'unexpected type', 3)
        
        txt = r'''  .segment text
                    .define 0x7, PQA
            '''
        self.assert_assembly_error(txt, 'unexpected type', 2)
    
    def test_global_directive_error(self):
        txt = r'''
                .segment text
                .global 12
            '''
        self.assert_assembly_error(txt, 'unexpected type', 3)
        
        txt = r'''
                .segment text
            ax: nop
                .global brap
            '''
        self.assert_assembly_error(txt, 'unknown label', 4)
    
    def test_byte_directive_error(self):
        txt = r'''
                .segment s
                .byte 5, 6, 9, ak
            '''
        self.assert_assembly_error(txt, 'argument 4 not a valid', 3)
        
        txt = r'''  .segment t
                    .byte 5, 9, 256, 4, 5, 6
            '''
        self.assert_assembly_error(txt, 'argument 3 not a valid', 2)
    
    def test_word_directive_error(self):
        txt = r'''
                .segment s
                .word k5, 6, 9, ak
            '''
        self.assert_assembly_error(txt, 'argument 1 not a valid', 3)
        
        txt = r'''  .segment t
                    .word 5, 9, 256, 4, 5, 699799799799799
            '''
        self.assert_assembly_error(txt, 'argument 6 not a valid', 2)

if __name__ == '__main__':
    unittest.main() 

