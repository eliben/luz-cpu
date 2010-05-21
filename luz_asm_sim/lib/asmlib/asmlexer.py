# Lexer for the assembly language
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#

import re
import sys

import ply.lex
from ply.lex import TOKEN


class AsmLexer(object):
    def __init__(self, error_func):
        self.error_func = error_func
        
    def build(self, **kwargs):
        """ Builds the lexer from the specification. Must be 
            called after the lexer object is created.
        """
        self.lexer = ply.lex.lex(object=self, **kwargs)
        
    def input(self, text):
        self.lexer.input(text)
    
    def token(self):
        return self.lexer.token()
    
    def reset_lineno(self):
        self.lexer.lineno = 1

    #######################--  PRIVATE --#######################

    tokens = (
        'ID', 'DIRECTIVE', 
        'NEWLINE',
        'DEC_NUM', 'HEX_NUM',
        'STRING',
        'COLON', 'COMMA',
        'LPAREN', 'RPAREN',
    )
    
    ##
    ## Regexes for use in tokens
    ##
    identifier = r'[a-zA-Z_\$][0-9a-zA-Z_]*'
    directive = r'\.'+identifier
    
    escape_char = r'\\["\\nt]'
    string_char = r'([^"\\\n]|'+escape_char+')'
    string = '"'+string_char+'*"'
    
    ##
    ## Token rules
    ##
    t_COLON     = r':'
    t_COMMA     = r','
    t_LPAREN    = r'\('
    t_RPAREN    = r'\)'
    
    t_ignore    = ' \t'
    
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count('\n')
        return t
    
    def t_COMMENT(self, t):
        r'\#.*'
        pass
    
    @TOKEN(string)
    def t_STRING(self, t):
        t.value = self._translate_string(t.value)
        return t
    
    @TOKEN(identifier)
    def t_ID(self, t):
        t.value = t.value.lower()
        return t

    @TOKEN(directive)
    def t_DIRECTIVE(self, t):
        t.value = t.value.lower()
        return t

    def t_HEX_NUM(self, t):
        r'\-?0[xX][0-9a-fA-F]+'
        t.value = int(t.value, 16)
        return t    

    def t_DEC_NUM(self, t):
        r'\-?\d+'
        t.value = int(t.value)
        return t

    def t_error(self, t):
        msg = 'Illegal character %s (at %s)' % (
            repr(t.value[0]), self._make_tok_location(t))
        self._error(msg)

    ##
    ## Internal methods
    ##
    def _error(self, msg):
        self.error_func(msg)
        self.lexer.skip(1)
        
    def _make_tok_location(self, t):
        return 'line %s' % t.lineno

    _trans_str_table = {
        'n':    '\n',
        't':    '\t',
        '\\':   '\\',
        '"':    '"'
    }

    def _translate_string(self, s):
        """ Given a string as accepted by the lexer, translates
            it into a real string (truncates "s, inserts real 
            escape characters where needed).
        """
        t = ''
        escape = False
        
        for i, c in enumerate(s[1:-1]):
            if escape:
                t += self._trans_str_table[c]
                escape = False
            else:
                if c == '\\':
                    escape = True
                else:
                    t += c
                    escape = False
        
        return t

