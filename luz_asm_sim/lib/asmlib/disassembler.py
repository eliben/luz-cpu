# A disassembler for Luz. 
# Converts binary words into mnemonic assembly instructions
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
import pprint, os, sys
from collections import defaultdict


from ..commonlib.utils import (
    extract_bitfield, signed2int)
from ..commonlib.luz_opcodes import *
from .asm_instructions import register_alias_of

class DisassembleError(Exception): pass


def disassemble(word, replace_alias=False):
    """ Given a word (32-bit integer) returns the mnemonic 
        assembly instruction it represents, as a string.
        
        replace_alias:
            If True, register numbers are replaced with their
            aliases.
        
        DisassembleError can be raised in case of errors.
    """
    # the opcode
    opcode = extract_bitfield(word, 31, 26)
    
    regnamer = _reg_name_alias if replace_alias else _reg_name_normal
    
    # dispatch 
    if opcode in _OP:
        dispatch = _OP[opcode]
        func, name = dispatch[0], dispatch[1]
        return func(word, name, regnamer)
    else:
        raise DisassembleError('unknown opcode %X' % opcode)


##################################################################


def _reg_name_normal(regnum):
    return '$r%s' % regnum

def _reg_name_alias(regnum):
    return register_alias_of[regnum]


def _dis_generic_3reg(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    rs = extract_bitfield(word, 20, 16)
    rt = extract_bitfield(word, 15, 11)
    return '%s %s, %s, %s' % (name, regnamer(rd), regnamer(rs), regnamer(rt))


def _dis_generic_2reg_imm(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    rs = extract_bitfield(word, 20, 16)
    imm16 = extract_bitfield(word, 15, 0)
    return '%s %s, %s, 0x%X' % (name, regnamer(rd), regnamer(rs), imm16)


def _dis_generic_1reg_imm(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    imm16 = extract_bitfield(word, 15, 0)
    return '%s %s, 0x%X' % (name, regnamer(rd), imm16)


def _dis_generic_1reg(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    return '%s %s' % (name, regnamer(rd))


def _dis_call(word, name, regnamer):
    imm26 = extract_bitfield(word, 25, 0)
    # annotate with the actual jump address (multiplied by 4)
    return '%s 0x%X [0x%X]' % (name, imm26, imm26 * 4)


def _dis_generic_offset26(word, name, regnamer):
    offset = signed2int(extract_bitfield(word, 25, 0))
    return '%s %d' % (name, offset)


def _dis_load(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    rs = extract_bitfield(word, 20, 16)
    offset = signed2int(extract_bitfield(word, 15, 0), nbits=16)
    return '%s %s, %d(%s)' % (name, regnamer(rd), offset, regnamer(rs))


def _dis_store(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    rs = extract_bitfield(word, 20, 16)
    offset = signed2int(extract_bitfield(word, 15, 0), nbits=16)
    return '%s %s, %d(%s)' % (name, regnamer(rs), offset, regnamer(rd))


def _dis_noop(word, name, regnamer):
    return '%s' % name


def _dis_branch(word, name, regnamer):
    rd = extract_bitfield(word, 25, 21)
    rs = extract_bitfield(word, 20, 16)
    offset = signed2int(extract_bitfield(word, 15, 0), nbits=16)
    return '%s %s, %s, %d' % (name, regnamer(rd), regnamer(rs), offset)


# Maps opcodes to functions that dissasemble them
#
_OP = {
    OP_ADD:     (_dis_generic_3reg, 'add'),
    OP_ADDI:    (_dis_generic_2reg_imm, 'addi'),
    OP_SUB:     (_dis_generic_3reg, 'sub'),
    OP_SUBI:    (_dis_generic_2reg_imm, 'subi'),
    OP_MULU:    (_dis_generic_3reg, 'mulu'),
    OP_MUL:     (_dis_generic_3reg, 'mul'),
    OP_DIVU:    (_dis_generic_3reg, 'divu'),
    OP_DIV:     (_dis_generic_3reg, 'div'),
    OP_LUI:     (_dis_generic_1reg_imm, 'lui'),
    OP_SLL:     (_dis_generic_3reg, 'sll'),
    OP_SLLI:    (_dis_generic_2reg_imm, 'slli'),
    OP_SRL:     (_dis_generic_3reg, 'srl'),
    OP_SRLI:    (_dis_generic_2reg_imm, 'srli'),
    OP_AND:     (_dis_generic_3reg, 'and'),
    OP_ANDI:    (_dis_generic_2reg_imm, 'andi'),
    OP_OR:      (_dis_generic_3reg, 'or'),
    OP_ORI:     (_dis_generic_2reg_imm, 'ori'),
    OP_NOR:     (_dis_generic_3reg, 'nor'),
    OP_XOR:     (_dis_generic_3reg, 'xor'),
    OP_LB:      (_dis_load, 'lb'),
    OP_LH:      (_dis_load, 'lh'),
    OP_LW:      (_dis_load, 'lw'),
    OP_LBU:     (_dis_load, 'lbu'),
    OP_LHU:     (_dis_load, 'lhu'),
    OP_SB:      (_dis_store, 'sb'),
    OP_SH:      (_dis_store, 'sh'),
    OP_SW:      (_dis_store, 'sw'),
    OP_JR:      (_dis_generic_1reg, 'jr'),
    OP_CALL:    (_dis_call, 'call'),
    OP_B:       (_dis_generic_offset26, 'b'),
    OP_BEQ:     (_dis_branch, 'beq'),
    OP_BNE:     (_dis_branch, 'bne'),
    OP_BGE:     (_dis_branch, 'bge'),
    OP_BGT:     (_dis_branch, 'bgt'),
    OP_BLE:     (_dis_branch, 'ble'),
    OP_BLT:     (_dis_branch, 'blt'),    
    OP_BGEU:    (_dis_branch, 'bgeu'),
    OP_BGTU:    (_dis_branch, 'bgtu'),
    OP_BLEU:    (_dis_branch, 'bleu'),
    OP_BLTU:    (_dis_branch, 'bltu'),
    OP_ERET:    (_dis_noop, 'eret'),
    OP_HALT:    (_dis_noop, 'halt'),
}


