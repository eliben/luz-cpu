""" Some utilities for working with VHDL 
"""
from __future__ import with_statement
import re

from lexer import Token, Lexer, LexerError


def vhdl_unit_name(file):
    """ Given the name of a VHDL file, attempts to find the unit
        (entity or package) name in this file.
        
        If several units are present, the first is returned.
        None is returned if no unit name is found.
    """
    rules = [
        ('--[^\n]*\n',  'COMMENT'),
        ('\n+',         'NEWLINE'),
        ('\w+',         'ID'),
        ('\s+',         'WHITESPACE'),
        ('[^\w\n]+',    'NONE'),
    ]

    lx = Lexer(rules, skip_whitespace=False)
    lx.input(open(file).read())
    
    window = [None, None, None]
    
    try:
        for tok in lx.tokens():
            # Implements a simple sliding window looking for 
            # (entity|package) <name> is
            # as 3 consecutive IDs
            #
            if tok.type == 'ID':
                window = window[1:3] + [tok.val.lower()]
                
                if (    window[0] in ('entity', 'package') and 
                        window[2] == 'is'):
                    return window[1]
    except LexerError, err:
        return None
    
    return None


def bool2vhdl(v):
    """ Creates a VHDL boolean value out of a Python boolean
        value.
    """
    return 'true' if v else 'false'


def num2vhdl_slv(num, width=4):
    """ Creates a VHDL slv (standard_logic_vector) string from
        a number. The width in bytes can be specified.
        
        Examples:
            num2vhdl_slv(10, width=1) => x"0A"
            num2vhdl_slv(0x10, width=2) => x"0010"
    """
    return ('x"%0' + str(width * 2) + 'X"') % num
    

def vhdl_slv2num(slv):
    """ Given a VHDL slv string, returns the number it represents.
    """
    is_hex = slv.startswith('x')
    return int(slv.lstrip('x').strip('"'), 16 if is_hex else 2)


class IncorrectTimeError(Exception): pass

def verify_time_str(time_str):
    """ If time_str is not a valid VHDL-type time string (such
        as '100 ns', '40 ms', etc.), IncorrectTimeError is thrown.
    """
    m = re.match('\d+ \s+ (\w+)', time_str, re.X)
    if m:
        units = m.group(1).lower()
        if units not in ['ps', 'ns', 'us', 'ms', 'sec']:
            raise IncorrectTimeError('%s -- bad time units' % time_str)
    else:
        raise IncorrectTimeError(time_str)


def time2ns(time_str):
    """ Given a VHDL-type time string, converts it to the number
        of nanoseconds it represents. Assumes time_str is a valid
        time string.
        
        For example: '13 us' => 13000
    """
    mul = {
        'ps':   0,
        'ns':   1,
        'us':   1000,
        'ms':   1000 * 1000,
        'sec':  1000 * 1000 * 1000
    }
    
    num, units = time_str.split()
    return int(num) * mul[units]
    

class UpdateTransactorError(Exception): pass

def update_vhdl_transactor_file(
        filename, 
        trans_lines, 
        start_marker='@@ begin transactor',
        end_marker='@@ end transactor'
    ):
    """ Updates the VHDL file that serves to list auto-generated
        transactions.
        
        filename:
            The name of the VHDL file
        
        trans_lines:
            A list of transaction lines (VHDL code). Newlines will
            be appended automatically
        
        start_marker, end_marker:
            Patterns to look for in the file to specify the 
            beginning and end of the auto-generated section.
    """
    with open(filename) as infile:
        file_lines = infile.readlines()

    n_start = -1
    n_end = -1

    for i, line in enumerate(file_lines):
        if line.find(start_marker) >= 0:
            n_start = i
            
            # Find out the indentation of the start marker line,
            # to align all the transactor lines to it
            #
            m = re.match('(\s*)\S', line)
            if m:
                indent = m.group(1)
            else:
                indend = ''
        elif line.find(end_marker) >= 0:
            n_end = i
    
    if n_start < 0:
        raise UpdateTransactorError('no start marker found')
    elif n_end < 0:
        raise UpdateTransactorError('no end marker found')
    
    trans_lines = [indent + ln + '\n' for ln in trans_lines]
    all_lines = (   file_lines[:n_start+1] + 
                    [indent + '\n'] +
                    trans_lines + 
                    [indent + '\n'] +
                    file_lines[n_end:])
    
    with open(filename, 'w') as outfile:
        outfile.writelines(all_lines)


if __name__ == '__main__':
    #~ print vhdl_unit_name('slave_fpga.vhd')
    print time2ns('12 ps')
    


    
    