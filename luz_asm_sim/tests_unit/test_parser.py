import re
import sys
import unittest

import setup_path
from lib.asmlib.asmparser import *


class ExpandError(Exception): pass
    

def expand_parsed(ir):
    """ Expands the inetermediate form object returned by the 
        parser into a nested list that's simple to use in unit
        tests.
        
        Returns a list of 'lines'. Each line is a list of 3 
        elements: [label, name, args]
        
        label:
            line label, or '' if none
        
        name:
            instruction/directive name, or '' if none
        
        args:
            list of instruction/directive arguments, or [] if none
    """
    rfile = []
    for inst in ir:
        if not inst: continue
        
        rargs = []
        for arg in inst.args:
            if type(arg) == Number:
                rargs.append(arg.val)
            elif type(arg) == Id:
                rargs.append(arg.id)
            elif type(arg) == String:
                rargs.append(arg.val)
            elif type(arg) == MemRef:
                rargs.append([arg.offset.val, arg.id.id])
            else:
                raise ExpandError
                
        rinst = [
            inst.label or '',
            inst.name or '',
            rargs]
        rfile.append(rinst)
    
    return rfile


class TestAsmParser(unittest.TestCase):
    def setUp(self):
        self.parser = AsmParser()

    def parse(self, txt):
        return self.parser.parse(txt)
    
    def expand(self, txt):
        return expand_parsed(self.parse(txt))
        
    def test_smoke(self):
        self.assertEqual(self.expand('lab: # commento'),
            [['lab', '', []]])
        
        self.assertEqual(self.expand('add 6'),
            [['', 'add', [6]]])
        
        self.assertEqual(self.expand('.ascii'),
            [['', '.ascii', []]])

        self.assertEqual(self.expand('lab: mul'),
            [['lab', 'mul', []]])

        self.assertEqual(self.expand('lab: .direc'),
            [['lab', '.direc', []]])

    def test_args(self):
        self.assertEqual(self.expand('add r6, r2, $r3'),
            [['', 'add', ['r6', 'r2', '$r3']]])
        
        self.assertEqual(self.expand('ll: add 0x25, $r9'),
            [['ll', 'add', [37, '$r9']]])

        self.assertEqual(self.expand('lhi 0x25'),
            [['', 'lhi', [37]]])

        self.assertEqual(self.expand('div 1, 2 #comcom!!!&*'),
            [['', 'div', [1, 2]]])

        self.assertEqual(self.expand('add 6(ti), r8, 0x12(r0)'),
            [['', 'add', [[6, 'ti'], 'r8', [18, 'r0']]]])

        self.assertEqual(self.expand(r'.ascii "abori\n", 2'),
            [['', '.ascii', ['abori\n', 2]]])

        self.assertEqual(self.expand(r'.segment naggu'),
            [['', '.segment', [r'naggu']]])

    def test_multiple_lines(self):
        self.assertEqual(self.expand(r'''
                    .data
            item:   .word 1
                    .text
                    .globl  main # Must be global
            main:   lui r15, 0x4423
                    call printf
            '''),
            [
                ['', '.data', []], 
                ['item', '.word', [1]], 
                ['', '.text', []], 
                ['', '.globl', ['main']], 
                ['main', 'lui', ['r15', 17443]], 
                ['', 'call', ['printf']]]
            )

        self.assertEqual(self.expand(r'''
                    .text
                    .align 2
                    .globl main
            main:
                    subu $sp, $sp, 32
                    sw ra, 20(sp)
                    sd a0, 32(sp)
                    sw 0, 24(sp)
                    sw 0, 28(sp)
            loop:
                    lw t6, 28(sp)
                    mul t7, t6, t6
                    lw t8, 24(sp)
                    addu t9, t8, t7
                    sw t9, 24(sp)
                    addu t0, t6, 1
                    sw t0, 28(sp)
                    ble t0, 100, loop
                    la a0, str
                    lw a1, 24(sp)
                    jal printf
                    move v0, 0
                    lw $ra, 20(sp)
                    addu sp, sp, 32
                    jr ra
                    .data
                    .align 0
            str:
                    .asciiz "The sum from 0 .. 100 is %d\n"
            '''),
            [
                ['', '.text', []], 
                ['', '.align', [2]], 
                ['', '.globl', ['main']], 
                ['main', '', []], 
                ['', 'subu', ['$sp', '$sp', 32]], 
                ['', 'sw', ['ra', [20, 'sp']]], 
                ['', 'sd', ['a0', [32, 'sp']]], 
                ['', 'sw', [0, [24, 'sp']]], 
                ['', 'sw', [0, [28, 'sp']]], 
                ['loop', '', []], 
                ['', 'lw', ['t6', [28, 'sp']]], 
                ['', 'mul', ['t7', 't6', 't6']], 
                ['', 'lw', ['t8', [24, 'sp']]], 
                ['', 'addu', ['t9', 't8', 't7']], 
                ['', 'sw', ['t9', [24, 'sp']]], 
                ['', 'addu', ['t0', 't6', 1]], 
                ['', 'sw', ['t0', [28, 'sp']]], 
                ['', 'ble', ['t0', 100, 'loop']], 
                ['', 'la', ['a0', 'str']], 
                ['', 'lw', ['a1', [24, 'sp']]], 
                ['', 'jal', ['printf']], 
                ['', 'move', ['v0', 0]], 
                ['', 'lw', ['$ra', [20, 'sp']]], 
                ['', 'addu', ['sp', 'sp', 32]], 
                ['', 'jr', ['ra']], 
                ['', '.data', []], 
                ['', '.align', [0]], 
                ['str', '', []], 
                ['', '.asciiz', ['The sum from 0 .. 100 is %d\n']]]
            )
        
    def test_lineno(self):
        self.assertEqual(self.parse('lab:')[0].lineno, 1)

        t1 = self.parse(r'''
                    .data
                    # comment
                    
            item:   .word 1
            
            
                    .text
                    .globl  main # Must be global
            main:   lui r15, 0x4423
                    call printf
            ''')
        
        self.assertEqual(t1[0].lineno, 2)
        self.assertEqual(t1[1].lineno, 5)
        self.assertEqual(t1[2].lineno, 8)
        self.assertEqual(t1[5].lineno, 11)
        
        t2 = self.parse('\n' * 8000 + '.data')
        self.assertEqual(t2[0].lineno, 8001)


class TestAsmParserErrors(unittest.TestCase):
    def setUp(self):
        self.parser = AsmParser()

    def parse(self, txt):
        return self.parser.parse(txt)

    def assert_error_at_line(self, msg, lineno):
        m = re.search('line (\d+)\)$', msg)
        if m:
            self.assertEqual(int(m.group(1)), lineno)
        else:
            self.fail('no line found in: "%s"' % msg)

    def assert_parse_error(self, txt, lineno):
        try:
            self.parse(txt)
        except ParseError:
            err = sys.exc_info()[1]
            err_msg = str(err)
            self.assert_error_at_line(err_msg, lineno)
        else:
            self.fail('ParseError not raised')
            
    def test_lexer_errors(self):
        self.assert_parse_error('%', 1)
        self.assert_parse_error('^', 1)
        self.assert_parse_error('\n*', 2)
        self.assert_parse_error(r'''
                    .data
                    # comment
                    
            item:   .word 1
            %''', 6)
    
    def test_parser_errors(self):
        self.assert_parse_error(r'''
                    .data
            item:   .word 1
                    .text
                    15
                    addu r1, r2, r3
            ''', 5)
        
        self.assert_parse_error(r'''
                :blinches    .data
            ''', 2)
        
        # expected comma between 'abc' and 12
        self.assert_parse_error(r'''
                .define abc 12
            ''', 2)


if __name__ == '__main__':
    unittest.main()


