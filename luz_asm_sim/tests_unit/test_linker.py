import os, sys, unittest
import setup_path
from lib.asmlib.linker import *
from lib.asmlib.assembler import *
from lib.asmlib.asm_common_types import *
from lib.commonlib.utils import *
from lib.commonlib.luz_defs import (
    USER_MEMORY_START, USER_MEMORY_SIZE)


# Initial offset
IOF = 0x100000

op_call = 0x1D
op_lui = 0x06
op_ori = 0x2A
op_add = 0x0
op_sub = 0x1


class TestLinker(unittest.TestCase):
    def setUp(self):
        self.asm = Assembler()
        self.linker = Linker(IOF)

    def assemble(self, txt):
        return self.asm.assemble(txt)
        
    def link(self, object_files):
        return self.linker.link(object_files)
    
    def test_collect_exports(self):
        obj = [0, 0, 0]
        obj[0] = self.assemble(r'''
                    .segment my1
            kwa:    .word 1
            kaw:    .word 1
                    .global kwa
                    .global kaw
            ''')
        
        obj[1] = self.assemble(r'''
                    .segment my1
            kaw:    .word 1
            kwa14:  .word 1
                    .global kwa14
            ''')
        
        obj[2] = self.assemble(r'''
                    .segment my1
                    .word 1
            jaxx:   .word 1
            
                    .global jaxx
                    .global karma
                    .global rarma
                    
                    .segment chipper
            karma:  .alloc 20
            rarma:  .alloc 20
            ''')
        
        self.assertEqual(self.linker._collect_exports(obj),
            {
             'kaw': (0, SegAddr(segment='my1', offset=4)),
             'kwa': (0, SegAddr(segment='my1', offset=0)),
             'kwa14': (1, SegAddr(segment='my1', offset=4)),
             'jaxx': (2, SegAddr(segment='my1', offset=4)),
             'karma': (2, SegAddr(segment='chipper', offset=0)),
             'rarma': (2, SegAddr(segment='chipper', offset=20))
            })
    
    def test_compute_segment_map(self):
        # Basic sanity check
        #
        obj1 = self.assemble(r'''
                    .segment joe
                add $r0, $r0, $r0
                xor $r5, $r5, $r7
            ''')
        
        obj2 = self.assemble(r'''
                    .segment moe
                .alloc 4
                    .segment joe
                and $r8, $r9, $r1
            ''')
        
        self.assertEqual(
            self.linker._compute_segment_map([obj1, obj2], IOF)[0],
            [
                {
                    'joe':  IOF,
                },
                {
                    'joe':  IOF + 8,
                    'moe':  IOF + 12
                }
            ])
        
        # A more convoluted case with 2 files
        #
        obj1 = self.assemble(r'''
                    .segment text
                add $r1, $r0, $r1
                .alloc 11
                    .segment data
                .word 0x1, 0x2, 0x3
            ''')
        
        obj2 = self.assemble(r'''
                    .segment junk
                .alloc 500
                .alloc 500
                    .segment data
                .word 0x90, 0x80, 0x90, 0x80, 0x80
                    .segment text
                add $r1, $r0, $r2
                add $r1, $r0, $r2
                add $r1, $r0, $r2
                add $r1, $r0, $r2
            ''')
    
        self.assertEqual(
            self.linker._compute_segment_map([obj1, obj2], IOF)[0],
            [
                {  
                    'data':     IOF,
                    'text':     IOF + 32 + 1000,
                },
                {
                    'data':     IOF + 12,
                    'junk':     IOF + 32,
                    'text':     IOF + 32 + 1000 + 16
                }
            ])

    def test_patch_segment_data(self):
        #
        #---- test CALL patch ----
        #
        obj1 = self.assemble(r'''
                    .segment junk
                add $r1, $r0, $r2
                .alloc 4
                call bomba
                .alloc 8
            datum: 
                .word 50, 60, 70, 80
                call datum
            ''')
        
        seg_data = obj1.seg_data['junk']
        saved_seg_data = seg_data[:]
        
        # Perform "import patching"
        #
        self.linker._patch_segment_data(
            seg_data=seg_data,
            instr_offset=8, 
            type=ImportType.CALL,
            mapped_address=0x65434)
        
        # make sure the patch is correct
        instr = bytes2word(seg_data[8:12])
        self.assertEqual(extract_bitfield(instr, 31, 26), op_call)
        self.assertEqual(extract_bitfield(instr, 25, 0), 0x65434/4)
        
        # make sure nothing else was changed
        self.assertEqual(seg_data[0:8], saved_seg_data[0:8])
        self.assertEqual(seg_data[12:], saved_seg_data[12:])
        
        # Now perform "relocation patching" on 'datum'
        #
        saved_seg_data = seg_data[:]
        self.linker._patch_segment_data(
            seg_data=seg_data,
            instr_offset=36, 
            type=RelocType.CALL,
            mapped_address=0x100000)
        
        instr = bytes2word(seg_data[36:40])
        self.assertEqual(extract_bitfield(instr, 31, 26), op_call)
        self.assertEqual(extract_bitfield(instr, 25, 0), 0x100000/4+5)
        self.assertEqual(seg_data[0:36], saved_seg_data[0:36])
        
        #
        #---- test LI patch ----
        #
        obj2 = self.assemble(r'''
                    .segment tiexto
                add $r1, $r0, $r2
                .alloc 8
                li $r28, far_symbol
                .alloc 8000
            datum: 
                .word 50, 60, 70, 80
                li $r20, datum
            ''')
        
        seg_data = obj2.seg_data['tiexto']
        
        # Perform "import patching"
        #
        saved_seg_data = seg_data[:]
        self.linker._patch_segment_data(
            seg_data=seg_data,
            instr_offset=12, 
            type=ImportType.LI,
            mapped_address=0xDEADBEEF)
        
        # make sure the patch is correct
        lui_instr = bytes2word(seg_data[12:16])
        self.assertEqual(extract_bitfield(lui_instr, 31, 26), op_lui)
        self.assertEqual(extract_bitfield(lui_instr, 15, 0), 0xDEAD)
        ori_instr = bytes2word(seg_data[16:20])
        self.assertEqual(extract_bitfield(ori_instr, 31, 26), op_ori)
        self.assertEqual(extract_bitfield(ori_instr, 15, 0), 0xBEEF)
        
        # make sure nothing else was changed
        self.assertEqual(seg_data[0:12], saved_seg_data[0:12])
        self.assertEqual(seg_data[20:], saved_seg_data[20:])

        # Perform "relocation patching"
        #
        saved_seg_data = seg_data[:]
        self.linker._patch_segment_data(
            seg_data=seg_data,
            instr_offset=8036, 
            type=RelocType.LI,
            mapped_address=0xDEADBEEF)
        
        # make sure the patch is correct
        lui_instr = bytes2word(seg_data[8036:8040])
        self.assertEqual(extract_bitfield(lui_instr, 31, 26), op_lui)
        self.assertEqual(extract_bitfield(lui_instr, 15, 0), 0xDEAD)
        ori_instr = bytes2word(seg_data[8040:8044])
        self.assertEqual(extract_bitfield(ori_instr, 31, 26), op_ori)
        self.assertEqual(extract_bitfield(ori_instr, 15, 0), 8020+0xBEEF)
        
        # make sure nothing else was changed
        self.assertEqual(seg_data[0:8036], saved_seg_data[0:8036])
        self.assertEqual(seg_data[8044:], saved_seg_data[8044:])

    def test_resolve_relocations(self):
        obj1 = self.assemble(r'''
                    .segment joe
                add $r0, $r0, $r0
                add $r0, $r0, $r0
            margie:
                xor $r5, $r5, $r7
            burka:
                .word 0x70
                    .segment moe
                call margie
                li $r20, burka
            ''')
        
        segment_map, total_size = self.linker._compute_segment_map([obj1], IOF)
        self.assertEqual(segment_map,
            [
                {
                    'joe':  IOF,
                    'moe':  IOF + 16,
                },
            ])
        self.assertEqual(total_size, 28)
        
        
        moe_data = obj1.seg_data['moe']
        
        # make sure that nominally the instructions are what we 
        # expect.
        #
        call_instr = bytes2word(moe_data[0:4])
        self.assertEqual(call_instr,
            build_bitfield(31, 26, op_call) |
            build_bitfield(25, 0, 8 / 4))
        
        lui_instr = bytes2word(moe_data[4:8])
        ori_instr = bytes2word(moe_data[8:12])
        self.assertEqual(extract_bitfield(lui_instr, 15, 0), 0)
        self.assertEqual(extract_bitfield(ori_instr, 15, 0), 12)
        
        # Now resolve the relocation
        #
        self.linker._resolve_relocations([obj1], segment_map)
        
        # check that the instruction's destination was relocated
        # properly
        #
        call_instr = bytes2word(moe_data[0:4])
        self.assertEqual(call_instr,
            build_bitfield(31, 26, op_call) |
            build_bitfield(25, 0, (IOF + 8) / 4))
    
        lui_instr = bytes2word(moe_data[4:8])
        ori_instr = bytes2word(moe_data[8:12])
        self.assertEqual(extract_bitfield(lui_instr, 15, 0), 0x10)
        self.assertEqual(extract_bitfield(ori_instr, 15, 0), 12)
    
    def test_resolve_imports(self):
        obj = [0, 0]
        obj[0] = self.assemble(r'''
                    .segment moe
            kaw:    .word 1
            kwa14:  .word 1
                    call karma
                    li $r20, jaxx
            ''')
        
        obj[1] = self.assemble(r'''
                    .segment my1
                    .word 1
            jaxx:   .word 1
            
                    .global jaxx
                    .global karma
                    .global rarma
                    
                    .segment chipper
            karma:  .alloc 20
            rarma:  .alloc 20
            ''')
        
        segment_map, total_size = self.linker._compute_segment_map(obj, IOF)
        exports = self.linker._collect_exports(obj)
        
        moe_data = obj[0].seg_data['moe']
        
        # make sure that nominally the instructions are what we 
        # expect.
        #
        call_instr = bytes2word(moe_data[8:12])
        self.assertEqual(extract_bitfield(call_instr, 25, 0), 0)
        lui_instr = bytes2word(moe_data[12:16])
        ori_instr = bytes2word(moe_data[16:20])
        self.assertEqual(extract_bitfield(lui_instr, 15, 0), 0)
        self.assertEqual(extract_bitfield(ori_instr, 15, 0), 0)
        
        # Now resolve the imports
        #
        self.linker._resolve_imports(obj, segment_map, exports)

        # check correct resolutions
        #
        chipper_addr = segment_map[1]['chipper']
        call_instr = bytes2word(moe_data[8:12])
        self.assertEqual(extract_bitfield(call_instr, 25, 0), 
            chipper_addr / 4)
        
        my1_addr = segment_map[1]['my1']
        lui_instr = bytes2word(moe_data[12:16])
        ori_instr = bytes2word(moe_data[16:20])
        self.assertEqual(extract_bitfield(lui_instr, 15, 0), 
            my1_addr >> 16)
        self.assertEqual(extract_bitfield(ori_instr, 15, 0), 
            (my1_addr & 0xFFFF) + 4)

    def test_link(self):
        obj0 = self.assemble(r'''
                    .segment moe
                    .global asm_main
            asm_main:
                    add $r5, $r6, $sp
            kaw:    .word 1
            kwa14:  .word 1
                    li $r20, kaw
            ''')
        
        linker = Linker(USER_MEMORY_START, USER_MEMORY_SIZE)
        image = linker.link([obj0])
        
        sp_ptr = IOF + USER_MEMORY_SIZE - 4
        
        # 12 bytes for __startup
        # 16 bytes in segment moe
        # 4 bytes for __heap
        # 
        self.assertEqual(len(image), 36)
        
        # The initial 'LI' pointing to $sp
        #
        lui_instr = bytes2word(image[0:4])
        self.assertEqual(lui_instr,
            build_bitfield(31, 26, op_lui) | 
            build_bitfield(25, 21, 29) |
            build_bitfield(15, 0, sp_ptr >> 16))
        
        ori_instr = bytes2word(image[4:8])
        self.assertEqual(ori_instr,
            build_bitfield(31, 26, op_ori) | 
            build_bitfield(25, 21, 29) |
            build_bitfield(20, 16, 29) |
            build_bitfield(15, 0, sp_ptr & 0xFFFF))
        
        # calling 'asm_main'
        # 'moe' will be mapped after __startup, so at 16
        call_instr = bytes2word(image[8:12])
        self.assertEqual(call_instr,
            build_bitfield(31, 26, op_call) | 
            build_bitfield(25, 0, (IOF + 12) / 4))
        
        # Now the first instruction of 'moe'
        # 
        add_instr = bytes2word(image[12:16])
        self.assertEqual(add_instr,
            build_bitfield(31, 26, op_add) |
            build_bitfield(25, 21, 5) |
            build_bitfield(20, 16, 6) |
            build_bitfield(15, 11, 29))
        

class TestLinkerErrors(unittest.TestCase):
    def setUp(self):
        self.asm = Assembler()
        self.linker = Linker(IOF)

    def assemble(self, txt):
        return self.asm.assemble(txt)
        
    def link(self, object_files):
        return self.linker.link(object_files)

    def assert_str_contains(self, str, what):
        self.failUnless(str.find(what) > -1, '"%s" contains "%s"' % (str, what))

    def assert_linker_error(self, objs, msg):
        try:
            self.link(objs)
        except LinkerError:
            err = sys.exc_info()[1]
            err_msg = str(err)
            self.assert_str_contains(err_msg, msg)
        else:
            self.fail('LinkerError not raised')

    def test_collect_exports_errors(self):
        obj1 = self.assemble(r'''
                    .segment text
            jaxx:   add $r1, $r0, $r1
                    .global jaxx
            ''')
        
        obj2 = self.assemble(r'''
                    .segment data
                    .global joe
                    .global jaxx
            jaxx:
            joe:
            ''')
        
        self.assert_linker_error([obj1, obj2], 'Duplicated export')
        
    def test_patch_segment_data_errors(self):
        obj1 = self.assemble(r'''
                    .segment junk
                add $r1, $r0, $r2
                .alloc 4
                call bomba
                li $r8, 1550505
                .alloc 8
            datum: 
                .word 50, 60, 70, 80
                call datum
            ''')
        
        seg_data = obj1.seg_data['junk']
        
        # "import patching" with offset to a wrong instruction
        #
        try:
            self.linker._patch_segment_data(
                seg_data=seg_data,
                instr_offset=12, 
                type=ImportType.CALL,
                mapped_address=0x65434)
        except LinkerError:
            err = sys.exc_info()[1]
            err_msg = str(err)
            self.assert_str_contains(err_msg, 'expected CALL')
        else:
            self.fail('LinkerError not raised')

    def test_link_errors(self):
        obj0 = self.assemble(r'''
                    .segment moe
            asm_main:
                    add $r5, $r6, $sp
            kaw:    .word 1
            kwa14:  .word 1
                    li $r20, kaw
            ''')
        
        # no global (exported) asm_main, although the label is
        # defined
        #
        self.assert_linker_error([obj0], "import of symbol 'asm_main")



#-----------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

