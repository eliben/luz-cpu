import sys
import unittest

import setup_path
from lib.asmlib.asmparser import *
from lib.asmlib import asmlexer


def token_list(lex):
    return list(iter(lex.token, None))


def all_token_types(lex):
    return [i.type for i in token_list(lex)]


class TestAsmLexer(unittest.TestCase):
    def assert_token_types(self, text, tokens):
        self.lexer.input(text)
        self.assertEqual(all_token_types(self.lexer), tokens)
    
    def assert_token(self, text, typeval):
        self.lexer.input(text)
        t = self.lexer.token()
        self.assertEqual(t.type, typeval[0])
        self.assertEqual(t.value, typeval[1])
    
    def setUp(self):
        def ef(msg):
            self.fail(msg)
        
        self.lexer = asmlexer.AsmLexer(error_func=ef)
        self.lexer.build()

    def test_punctuation(self):
        self.assert_token(':', ('COLON', ':'))
        self.assert_token_types(':,', ['COLON', 'COMMA'])
        self.assert_token_types(':(,))', 
            ['COLON', 'LPAREN', 'COMMA', 'RPAREN', 'RPAREN'])

    def test_numbers(self):
        self.assert_token('145', ('DEC_NUM', 145))
        self.assert_token('-145', ('DEC_NUM', -145))
        self.assert_token('0x145', ('HEX_NUM', 0x145))
        self.assert_token('-0x145', ('HEX_NUM', -0x145))
        self.assert_token('0xFA', ('HEX_NUM', 0xfa))
        self.assert_token('0xe56', ('HEX_NUM', 0xe56))
        self.assert_token('0xD234454D', ('HEX_NUM', 0xd234454d))
        
        self.assert_token_types('10,0x2,0xe,55',
            [   'DEC_NUM', 'COMMA', 'HEX_NUM', 'COMMA',
                'HEX_NUM', 'COMMA', 'DEC_NUM'])

    def test_ID_directive(self):
        self.assert_token('hello', ('ID', 'hello'))
        self.assert_token('heLLo', ('ID', 'hello'))
        self.assert_token('$heLLo', ('ID', '$hello'))
        self.assert_token('.heLLo', ('DIRECTIVE', '.hello'))

    def test_strings(self):
        self.assert_token('"joe"', ('STRING', 'joe'))
        self.assert_token(r'"line\n"', ('STRING', 'line\n'))
        self.assert_token(r'"\t\"jo\ne"', ('STRING', '\t"jo\ne'))
    
    def test_comments(self):
        self.assert_token_types('#122\n:', 
            ['NEWLINE', 'COLON'])

    def test_text(self):
        self.assert_token_types(r"""
                    .data
            item:   .word 1
                    .text
                    .globl  main # Must be global
            main:   lui $r15, 0x4423
                    call printf
            """,
            [   'NEWLINE', 
                'DIRECTIVE', 'NEWLINE',
                'ID', 'COLON', 'DIRECTIVE', 'DEC_NUM', 'NEWLINE',
                'DIRECTIVE', 'NEWLINE',
                'DIRECTIVE', 'ID', 'NEWLINE',
                'ID', 'COLON', 'ID', 'ID', 'COMMA', 'HEX_NUM', 'NEWLINE',
                'ID', 'ID', 'NEWLINE'])


if __name__ == '__main__':
    unittest.main() 

