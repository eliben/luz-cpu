# Parser for the assembly language
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#

import re
import sys

from collections import namedtuple
import ply.yacc

from .asmlexer import AsmLexer


##
## The following 'classes' are the intermediate form into which
## the parser reads the assembly code.
##
Number = namedtuple('Number', 'val')
Id = namedtuple('Id', 'id')
String = namedtuple('String', 'val')
MemRef = namedtuple('Memref', 'offset id')
Instruction = namedtuple('Instruction', 'label name args lineno')
Directive = namedtuple('Directive', 'label name args lineno')
LabelDef = namedtuple('LabelDef', 'label lineno')


class ParseError(Exception): pass


class AsmParser(object):
    """ Parses a chunk of assembly code into intermediate form.
        
        The grammar of the assembly language is context-free and 
        is defined by the following BNF:
            * terminals are UPPERCASE, non-terminals LOWECASE
            * ? specifies "optional"
            
        asm_file ::=
            asm_line
            asm_file asm_line
        
        asm_line ::=
            empty_line
            label_def NEWLINE
            directive NEWLINE 
            instruction NEWLINE
        
        empty_line ::=
            NEWLINE
        
        directive ::=
            label_def? DIRECTIVE arguments?
        
        instruction ::=
            label_def? ID arguments?
        
        label_def ::=
            ID COLON
        
        arguments ::= 
            argument
            arguments COMMA argument
        
        argument ::=
            ID
            number
            STRING
            number LPAREN ID RPAREN
        
        number ::= 
            DEC_NUM
            HEX_NUM
            
        The parser doesn't recognize specific assembly 
        instructions or directives, and doesn't know how many
        arguments each one expects. This will be checked at the 
        next level. 
        Therefore, the parser stays very general and allows for
        a flexible specification of instructions/directives, even
        dynamically in a user defined way (such as macros).
    """
    def __init__(self, yacctab='parsetab'):
        self.lexer = AsmLexer(error_func=self._lex_error_func)
        self.lexer.build()
        self.tokens = self.lexer.tokens
        
        self.parser = ply.yacc.yacc(module=self, tabmodule=yacctab)
        
    def parse(self, text):
        """ Parses assembly code into intermediate form.
            Returns a list of Instruction and Directive objects.
        """
        self.lexer.reset_lineno()
        # Parsing is line-oriented, so make sure the file always
        # ends with a new line.
        #
        return self.parser.parse(text + '\n', lexer=self.lexer)

    ######################--   PRIVATE   --######################

    def _lex_error_func(self, msg):
        raise ParseError(msg)

    ##
    ## Grammar productions
    ##
    def p_asm_file(self, p):
        ''' asm_file    : asm_line
                        | asm_file asm_line
        '''
        # skip empty lines
        if len(p) >= 3:
            p[0] = p[1] + [p[2]] if p[2] else p[1]
        else:
            p[0] = [p[1]] if p[1] else []
    
    def p_asm_line_1(self, p):
        ''' asm_line    : empty_line 
                        | directive NEWLINE 
                        | instruction NEWLINE
        '''
        p[0] = p[1]
    
    def p_asm_line_2(self, p):
        ''' asm_line : label_def NEWLINE
        '''
        p[0] = Instruction(
            label=p[1].label,
            name=None,
            args=[],
            lineno=p[1].lineno)
    
    def p_empty_line(self, p):
        ''' empty_line : NEWLINE '''
        p[0] = None
    
    def p_directive_1(self, p):
        ''' directive : label_def DIRECTIVE arguments_opt '''
        p[0] = Directive(
            label=p[1].label,
            name=p[2],
            args=p[3],
            lineno=p.lineno(2))

    def p_directive_2(self, p):
        ''' directive : DIRECTIVE arguments_opt '''
        p[0] = Directive(
            label=None,
            name=p[1],
            args=p[2],
            lineno=p.lineno(1))    
    
    def p_instruction_1(self, p):
        ''' instruction     : label_def ID arguments_opt '''
        p[0] = Instruction(
            label=p[1].label,
            name=p[2],
            args=p[3],
            lineno=p.lineno(2))
    
    def p_instruction_2(self, p):
        ''' instruction     : ID arguments_opt '''
        p[0] = Instruction(
            label=None,
            name=p[1],
            args=p[2],
            lineno=p.lineno(1))
    
    def p_label_def(self, p):
        ''' label_def   : ID COLON '''
        p[0] = LabelDef(p[1], p.lineno(1))
    
    def p_arguments_opt(self, p):
        ''' arguments_opt   : arguments
                            |
        '''
        p[0] = p[1] if len(p) >= 2 else []
    
    def p_arguments_1(self, p):
        ''' arguments   : argument '''
        p[0] = [p[1]]
    
    def p_arguments_2(self, p):
        ''' arguments   : arguments COMMA argument '''
        p[0] = p[1] + [(p[3])]
    
    def p_argument_1(self, p):
        ''' argument    : ID '''
        p[0] = Id(p[1])
        
    def p_argument_2(self, p):
        ''' argument    : STRING '''
        p[0] = String(p[1])
    
    def p_argument_3(self, p):
        ''' argument    : number '''
        p[0] = p[1]
    
    def p_argument_4(self, p):
        ''' argument    : number LPAREN ID RPAREN
        '''
        p[0] = MemRef(offset=p[1], id=Id(p[3]))

    def p_argument_5(self, p):
        ''' argument    : ID LPAREN ID RPAREN
        '''
        p[0] = MemRef(offset=Id(p[1]), id=Id(p[3]))

    def p_number(self, p):
        ''' number  : DEC_NUM
                    | HEX_NUM
        '''
        p[0] = Number(p[1])
    
    def p_error(self, p):
        next_t = ply.yacc.token()
        raise ParseError("invalid code before %s (at line %s)" % (
            repr(next_t.value), next_t.lineno))



