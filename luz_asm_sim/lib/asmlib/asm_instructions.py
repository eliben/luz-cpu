# Implementation of instruction assembly. 
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
import re

from .asm_common_types import ImportType, RelocType

from ..commonlib.utils import (
    extract_bitfield, num_fits_in_nbits, build_bitfield)

from ..commonlib.luz_opcodes import *
from ..commonlib.portability import is_int_type

class InstructionError(Exception): pass

   
def instruction_exists(name):
    """ Does such an instruction exist ?
    """
    return name in _INSTR

def instruction_length(name):
    """ The length of an instruction, in bytes.
    """
    return _INSTR[name]['len']


def assemble_instruction(name, args, addr, symtab, defines):
    """ Assembles the instruction.
    
        name:
            The instruction name.
        
        args:
            The arguments passed to the instruction.
        
        addr:
            A (segment, addr) pair, specifying the location into
            which the instruction is assembled.
        
        symtab:
            The label symbol table from the first pass of the 
            assembler.
        
        defines:
            A table of constants defined by the .define directive
        
        Returns an array of AssembledInstruction objects (most
        instructions assemble into a single AssembledInstruction,
        but some pseudo-instructions produce more than one).
        
        Throws InstructionError for errors in the instruction.
    """
    if not instruction_exists(name):
        raise InstructionError('Unknown instruction %s' % name)
    
    instr = _INSTR[name]
    
    if not instr['nargs'] == len(args):
        raise InstructionError('%s expected %d arguments' % (
                name, instr['nargs']))
    
    asm_instr = instr['func'](args, addr, symtab, defines)
    
    if isinstance(asm_instr, list):
        return asm_instr
    else:
        return [asm_instr]


class AssembledInstruction(object):
    def __init__(self, op=None, import_req=None, reloc_req=None):
        """ 
            op:
                Numeric representation of the assembled 
                instruction.
                
            import_req:
                An import request. Consists of a (type, symbol)
                pair, where type is the instruction requesting the
                import and symbol is the import symbol's name.
                None if no import is required.
                
            reloc_req:
                A relocation request. Consists of a 
                (type, segment) pair, where type is the 
                instruction requesting the relocation and segment
                is the segment name relative to which the 
                relocation is needed.
                None if no relocation is required
        """
        self.op = op
        self.import_req = import_req
        self.reloc_req = reloc_req

    def __repr__(self):
        str = 'AssembledInstruction: op=0x%08X' % self.op
        if self.import_req: 
            str += ', import_req=%s' % repr(self.import_req)
        if self.reloc_req: 
            str += ', reloc_req=%s' % repr(self.reloc_req)
        
        return str


#
##
###
####
#####
######
########################--   PRIVATE   --######################
######
#####
####
###
##
#

# The instruction table, filled in _build_instr_table.
# Maps instruction names to their properties:
# 
# nargs: 
#   The amount of arguments the instruction expects
# len:   
#   The amount of memory bytes the assembled instruction occupates
# op:
#   The opcode for this instruction. Pseudo-instructions have 
#   this set to None, because they use the opcodes of other 
#   instructions.
# func:
#   The function that assembles the instruction, given its 
#   arguments and additional information from the assembler.
#
_INSTR = {}

def _build_instr_table():
    global _INSTR
    
    _INSTR = {
        'add': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_ADD, 
            'func':     _instr_add
        },
        
        'addi': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_ADDI, 
            'func':     _instr_addi
        },
        
        'and': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_AND, 
            'func':     _instr_and
        },
        
        'andi': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_ANDI, 
            'func':     _instr_andi
        },

        'beq': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BEQ,
            'func':     _instr_beq
        },
        
        'beqz': {
            'nargs':    2, 
            'len':      4, 
            'op':       None,
            'func':     _instr_beqz
        },
        
        'b': {
            'nargs':    1,
            'len':      4,
            'op':       OP_B,
            'func':     _instr_b
        },
        
        'bge': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BGE,
            'func':     _instr_bge
        },

        'bgeu': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BGEU,
            'func':     _instr_bgeu
        },

        'bgt': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BGT,
            'func':     _instr_bgt
        },

        'bgtu': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BGTU,
            'func':     _instr_bgtu
        },

        'ble': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BLE,
            'func':     _instr_ble
        },

        'bleu': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BLEU,
            'func':     _instr_bleu
        },

        'blt': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BLT,
            'func':     _instr_blt
        },

        'bltu': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BLTU,
            'func':     _instr_bltu
        },

        'bne': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_BNE,
            'func':     _instr_bne
        },

        'bnez': {
            'nargs':    2, 
            'len':      4, 
            'op':       None,
            'func':     _instr_bnez
        },
        
        'call': {
            'nargs':    1,
            'len':      4,
            'op':       OP_CALL,
            'func':     _instr_call
        },
        
        'div': {
            'nargs':    3,
            'len':      4,
            'op':       OP_DIV,
            'func':     _instr_div
        },
        
        'divu': {
            'nargs':    3,
            'len':      4,
            'op':       OP_DIVU,
            'func':     _instr_divu
        },
        
        'eret': {
            'nargs':    0, 
            'len':      4, 
            'op':       OP_ERET,
            'func':     _instr_eret
        },

        'halt': {
            'nargs':    0, 
            'len':      4, 
            'op':       OP_HALT,
            'func':     _instr_halt
        },

        'jr': {
            'nargs':    1, 
            'len':      4, 
            'op':       OP_JR,
            'func':     _instr_jr
        },

        'lb': {
            'nargs':    2, 
            'len':      4, 
            'op':       OP_LB,
            'func':     _instr_lb
        },
        
        'lbu': {
            'nargs':    2, 
            'len':      4, 
            'op':       OP_LBU,
            'func':     _instr_lbu
        },        
        
        'lh': {
            'nargs':    2, 
            'len':      4, 
            'op':       OP_LH,
            'func':     _instr_lh
        },
        
        'lhu': {
            'nargs':    2, 
            'len':      4, 
            'op':       OP_LHU,
            'func':     _instr_lhu
        },
        
        'li': {
            'nargs':    2,
            'len':      8,
            'op':       None,
            'func':     _instr_li,
        },

        'lli': {
            'nargs':    2, 
            'len':      4, 
            'op':       None,
            'func':     _instr_lli
        },
        
        'lui': {
            'nargs':    2, 
            'len':      4, 
            'op':       OP_LUI,
            'func':     _instr_lui
        },

        'lw': {
            'nargs':    2, 
            'len':      4, 
            'op':       OP_LW,
            'func':     _instr_lw
        },
        
        'move': {
            'nargs':    2, 
            'len':      4, 
            'op':       None,
            'func':     _instr_move
        },
        
        'mul': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_MUL,
            'func':     _instr_mul
        },

        'mulu': {
            'nargs':    3, 
            'len':      4, 
            'op':       OP_MULU,
            'func':     _instr_mulu
        },
        
        'neg': {
            'nargs':    2, 
            'len':      4, 
            'op':       None,
            'func':     _instr_neg
        },
        
        'nop': {
            'nargs':    0,
            'len':      4,
            'op':       None,
            'func':     _instr_nop
        },
        
        'nor': {
            'nargs':    3,
            'len':      4,
            'op':       OP_NOR,
            'func':     _instr_nor
        },
        
        'not': {
            'nargs':    2,
            'len':      4,
            'op':       None,
            'func':     _instr_not
        },
        
        'or': {
            'nargs':    3,
            'len':      4,
            'op':       OP_OR,
            'func':     _instr_or
        },
        
        'ori': {
            'nargs':    3,
            'len':      4,
            'op':       OP_ORI,
            'func':     _instr_ori
        },
        
        'ret': {
            'nargs':    0, 
            'len':      4, 
            'op':       None,
            'func':     _instr_ret
        },
        
        'sb': {
            'nargs':    2,
            'len':      4,
            'op':       OP_SB,
            'func':     _instr_sb
        },
        
        'sh': {
            'nargs':    2,
            'len':      4,
            'op':       OP_SH,
            'func':     _instr_sh
        },
        
        'sll': {
            'nargs':    3,
            'len':      4,
            'op':       OP_SLL,
            'func':     _instr_sll
        },
        
        'slli': {
            'nargs':    3,
            'len':      4,
            'op':       OP_SLLI,
            'func':     _instr_slli
        },

        'srl': {
            'nargs':    3,
            'len':      4,
            'op':       OP_SRL,
            'func':     _instr_srl
        },
        
        'srli': {
            'nargs':    3,
            'len':      4,
            'op':       OP_SRLI,
            'func':     _instr_srli
        },
        
        'sub': {
            'nargs':    3,
            'len':      4,
            'op':       OP_SUB,
            'func':     _instr_sub
        },

        'subi': {
            'nargs':    3,
            'len':      4,
            'op':       OP_SUBI,
            'func':     _instr_subi
        },
        
        'sw': {
            'nargs':    2,
            'len':      4,
            'op':       OP_SW,
            'func':     _instr_sw
        },

        'xor': {
            'nargs':    3,
            'len':      4,
            'op':       OP_XOR,
            'func':     _instr_xor
        },

    }

def _opcode_of(instr_name):
    return _INSTR[instr_name]['op']


from .asmparser import (
    AsmParser, Id, Number, String, MemRef)


# The following functions are instruction constructors. Each 
# instruction has its own constructor. All instruction 
# constructors share an iterface:
# 
# ---------
# Arguments
# ---------
#
# args:
#   Instruction arguments, as passed from the parser. It is 
#   assumed that the amount of arguments is correct.
#
# For the rest: See documentation of assemble_instruction
# 
# ------------
# Return value
# ------------
# 
# Either a single AssembledInstruction object, or an array 
# thereof, in case of pseudo-instructions that assemble into
# several instructions.
#


def _instr_3reg(op, args):
    """ A template for all the basic 3-register instructions. 
        'op' is the exact opcode to insert into the assembled 
        instruction.
    """
    rd = _reg(args[0])
    rs = _reg(args[1])
    rt = _reg(args[2])
    
    return AssembledInstruction(
            op= build_bitfield(31, 26, op) |
                build_bitfield(25, 21, rd) |
                build_bitfield(20, 16, rs) |
                build_bitfield(15, 11, rt))


def _instr_add(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('add'), args)

def _instr_sub(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('sub'), args)

def _instr_mulu(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('mulu'), args)

def _instr_mul(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('mul'), args)

def _instr_divu(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('divu'), args)

def _instr_div(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('div'), args)

def _instr_sll(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('sll'), args)

def _instr_srl(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('srl'), args)

def _instr_and(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('and'), args)

def _instr_or(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('or'), args)

def _instr_nor(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('nor'), args)

def _instr_xor(args, instr_addr, symtab, defines):
    return _instr_3reg(_opcode_of('xor'), args)

def _instr_nop(args, instr_addr, symtab, defines):
    # Pseudo-instruction: ADD r0, r0, r0
    return _instr_3reg( _opcode_of('add'), 
                        [Id('$r0'), Id('$r0'), Id('$r0')])

def _instr_not(args, instr_addr, symtab, defines):
    # Pseudo-instruction: NOR rd, rs, rs
    return _instr_3reg( _opcode_of('nor'), 
                        [args[0], args[1], args[1]])

def _instr_move(args, instr_addr, symtab, defines):
    # Pseudo-instruction: ADD rd, rs, r0
    return _instr_3reg( _opcode_of('add'),
                        [args[0], args[1], Id('$r0')])

def _instr_neg(args, instr_addr, symtab, defines):
    # Pseudo-instruction: SUB rd, r0, rs
    return _instr_3reg( _opcode_of('add'),
                        [args[0], Id('$r0'), args[1]])


def _instr_2reg_imm(op, args, defines):
    """ A template for all the basic 2-register + immediate 
        instructions. 
        'op' is the exact opcode to insert into the assembled 
        instruction.
    """
    rd = _reg(args[0])
    rs = _reg(args[1])
    c16 = _define_or_const(args[2], defines)
    
    return AssembledInstruction(
            op= build_bitfield(31, 26, op) |
                build_bitfield(25, 21, rd) |
                build_bitfield(20, 16, rs) |
                build_bitfield(15, 0, c16))

def _instr_addi(args, instr_addr, symtab, defines):
    return _instr_2reg_imm(_opcode_of('addi'), args, defines)

def _instr_subi(args, instr_addr, symtab, defines):
    return _instr_2reg_imm(_opcode_of('subi'), args, defines)

def _instr_ori(args, instr_addr, symtab, defines):
    return _instr_2reg_imm(_opcode_of('ori'), args, defines)

def _instr_andi(args, instr_addr, symtab, defines):
    return _instr_2reg_imm(_opcode_of('andi'), args, defines)

def _instr_slli(args, instr_addr, symtab, defines):
    return _instr_2reg_imm(_opcode_of('slli'), args, defines)

def _instr_srli(args, instr_addr, symtab, defines):
    return _instr_2reg_imm(_opcode_of('srli'), args, defines)

def _instr_lli(args, instr_addr, symtab, defines):
    # Pseudo-instruction: ORI rd, r0, const16
    return _instr_2reg_imm( _opcode_of('ori'), 
                            [args[0], Id('$r0'), args[1]],
                            defines)


def _instr_lui(args, instr_addr, symtab, defines):
    rd = _reg(args[0])
    c16 = _define_or_const(args[1], defines)
    
    return AssembledInstruction(
            op= build_bitfield(31, 26, _opcode_of('lui')) |
                build_bitfield(25, 21, rd) |
                build_bitfield(20, 16, 0) |
                build_bitfield(15, 0, c16))


def _instr_load(op, args, defines):
    """ A template for all Load instructions. 
    """
    rd = _reg(args[0])
    rs, off16 = _memref(args[1], defines)
    
    return AssembledInstruction(
            op= build_bitfield(31, 26, op)   |
                build_bitfield(25, 21, rd)   |
                build_bitfield(20, 16, rs)   |
                build_bitfield(15, 0, off16))


def _instr_store(op, args, defines):
    """ A template for all Store instructions.
    """
    rs = _reg(args[0])
    rd, off16 = _memref(args[1], defines)
    
    return AssembledInstruction(
            op= build_bitfield(31, 26, op)   |
                build_bitfield(25, 21, rd)   |
                build_bitfield(20, 16, rs)   |
                build_bitfield(15, 0, off16))


def _instr_lb(args, instr_addr, symtab, defines):
    return _instr_load(_opcode_of('lb'), args, defines)

def _instr_lbu(args, instr_addr, symtab, defines):
    return _instr_load(_opcode_of('lbu'), args, defines)

def _instr_lh(args, instr_addr, symtab, defines):
    return _instr_load(_opcode_of('lh'), args, defines)

def _instr_lhu(args, instr_addr, symtab, defines):
    return _instr_load(_opcode_of('lhu'), args, defines)

def _instr_lw(args, instr_addr, symtab, defines):
    return _instr_load(_opcode_of('lw'), args, defines)

def _instr_sb(args, instr_addr, symtab, defines):
    return _instr_store(_opcode_of('sb'), args, defines)

def _instr_sh(args, instr_addr, symtab, defines):
    return _instr_store(_opcode_of('sh'), args, defines)

def _instr_sw(args, instr_addr, symtab, defines):
    return _instr_store(_opcode_of('sw'), args, defines)


def _instr_jr(args, instr_addr, symtab, defines):
    rd = _reg(args[0])
    
    return AssembledInstruction(
            op= build_bitfield(31, 26, _opcode_of('jr')) |
                build_bitfield(25, 21, rd) |
                build_bitfield(20, 0, 0))


def _instr_ret(args, instr_addr, symtab, defines):
    # Pseudo-instruction: JR $ra
    return _instr_jr([Id('$ra')], instr_addr, symtab, defines)


def _instr_b(args, instr_addr, symtab, defines):
    off26 = _branch_offset(args[0], 26, instr_addr, symtab)
    
    # Note: _branch_offset makes sure that the offset fits into
    # a signed 26-bit field, so it's OK to take out the low 26
    # bits from it with build_bitfield.
    # 
    return AssembledInstruction(
            op= build_bitfield(31, 26, _opcode_of('b')) |
                build_bitfield(25, 0, off26))


def _instr_branch(op, args, instr_addr, symtab):
    """ A template for all conditional relative branch 
        instructions. 
    """
    rd = _reg(args[0])
    rs = _reg(args[1])
    
    off16 = _branch_offset(args[2], 16, instr_addr, symtab)
    
    # Note: _branch_offset makes sure that the offset fits into
    # a signed 16-bit field, so it's OK to take out the low 16
    # bits from it with build_bitfield.
    # 
    return AssembledInstruction(
            op= build_bitfield(31, 26, op)  |
                build_bitfield(25, 21, rd)  |
                build_bitfield(20, 16, rs)  |
                build_bitfield(15, 0, off16))   


def _instr_beq(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('beq'), args, instr_addr, symtab)

def _instr_bne(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bne'), args, instr_addr, symtab)

def _instr_bge(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bge'), args, instr_addr, symtab)

def _instr_bgt(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bgt'), args, instr_addr, symtab)

def _instr_ble(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('ble'), args, instr_addr, symtab)

def _instr_blt(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('blt'), args, instr_addr, symtab)

def _instr_bgeu(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bgeu'), args, instr_addr, symtab)

def _instr_bgtu(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bgtu'), args, instr_addr, symtab)

def _instr_bleu(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bleu'), args, instr_addr, symtab)

def _instr_bltu(args, instr_addr, symtab, defines):
    return _instr_branch(_opcode_of('bltu'), args, instr_addr, symtab)

def _instr_beqz(args, instr_addr, symtab, defines):
    # Pseudo-instruction: implemented as BEQ with r0 as the
    # second argument
    #
    args = [args[0], Id('$r0'), args[1]]
    return _instr_branch(_opcode_of('beq'), args, instr_addr, symtab)

def _instr_bnez(args, instr_addr, symtab, defines):
    # Pseudo-instruction: implemented as BNE with r0 as the
    # second argument
    #
    args = [args[0], Id('$r0'), args[1]]
    return _instr_branch(_opcode_of('bne'), args, instr_addr, symtab)


def _instr_eret(args, instr_addr, symtab, defines):
    return AssembledInstruction(
            op= build_bitfield(31, 26, _opcode_of('eret')))

def _instr_halt(args, instr_addr, symtab, defines):
    return AssembledInstruction(
            op= build_bitfield(31, 26, _opcode_of('halt')))


def _instr_call(args, instr_addr, symtab, defines):
    # CALL accepts an absolute address or a label. The label can
    # either be external (not defined in the symbol table) or 
    # internal (defined in the symbol table).
    #
    # External labels:
    # We don't know what the address of an external label is.
    # Therefore, an import request is added into the assembled
    # instruction. This import request will be connected to this
    # instruction and the linker will patch the destination 
    # address when it becomes known.
    # 
    # Internal labels:
    # For internal labels a relocation is required. The label's
    # address will be inserted into the destination field of the
    # instruction, and a relocation request for the segment in
    # which the label is defined will be returned with the 
    # assembled instruction. This relocation request will be
    # seen by the linker that will patch the destination once the
    # relocation address of the segment becomes known.
    #
    opcode_field = build_bitfield(31, 26, _opcode_of('call'))
    
    if (isinstance(args[0], Number) or 
        (isinstance(args[0], Id) and args[0].id in defines)
        ):
        # Number or defined constant
        #
        num = _define_or_const(args[0], defines, 26)
        return AssembledInstruction(
                op=opcode_field | build_bitfield(25, 0, num))
    elif isinstance(args[0], Id):
        label = args[0].id
        
        if label in symtab:
            # Relocation: place the label value into the 
            # destination field, and specify a relocation for the
            # label's segment.
            #
            segment, addr = symtab[label]
            return AssembledInstruction(
                    op= opcode_field | 
                        build_bitfield(25, 0, addr / 4),
                    reloc_req=(RelocType.CALL, segment))
        else:
            # Import symbol: leave the destination field empty
            # and specify an import symbol in the assembled 
            # instruction.
            #
            return AssembledInstruction(
                    op=opcode_field,
                    import_req=(ImportType.CALL, label))
    else:
        raise InstructionError('Invalid CALL destination: %s' % args[0])


def _instr_li(args, instr_addr, symtab, defines):
    # Creates two instructions (LUI and ORI).
    # The handling of labels is similar to _instr_call, except 
    # that the import/relocation information is computed for the
    # LUI&ORI pair and a single import/reloc_req is created, only
    # for LUI.
    #
    if (isinstance(args[1], Number) or
        (isinstance(args[1], Id) and args[1].id in defines)
        ):
        num = _define_or_const(args[1], defines, 32)
        
        low_word = extract_bitfield(num, left=15, right=0)
        high_word = extract_bitfield(num, left=31, right=16)
        
        return [
            _instr_lui( [args[0], Number(high_word)],
                        instr_addr, symtab, defines),
            _instr_ori( [args[0], args[0], Number(low_word)], 
                        instr_addr, symtab, defines)
            ]
    elif isinstance(args[1], Id):
        label = args[1].id
        
        if label in symtab:
            # Relocation
            segment, addr = symtab[label]
            low_word = extract_bitfield(addr, left=15, right=0)
            high_word = extract_bitfield(addr, left=31, right=16)
            
            lui = _instr_lui(   [args[0], Number(high_word)],
                                instr_addr, symtab, defines)
            ori = _instr_ori(   [args[0], args[0], Number(low_word)],
                                instr_addr, symtab, defines)
            
            lui.reloc_req = (RelocType.LI, segment)
            return [lui, ori]
        else:
            # Import
            lui = _instr_lui(   [args[0], Number(0)],
                                instr_addr, symtab, defines)
            ori = _instr_ori(   [args[0], args[0], Number(0)],
                                instr_addr, symtab, defines)
            
            lui.import_req = (ImportType.LI, label)
            return [lui, ori]
    else:
        raise InstructionError('Invalid LI destination: %s' % args[1])

#
# The following functions are utilities for the use of the 
# instruction constructors.
#

def _branch_offset(arg, nbits, instr_addr, symtab):
    """ Constructor for relative branch offsets. Such an offset
        can either be specified as an integer or as a label.
        
        Integers are the simple case.
        For labels, the instruction address is queried for the
        segment and address of the instruction being assemblied,
        and the label is extracted from the symbol table. 
        The segments of the label and instruction must match, and
        the offset between them must be small enough to fit into
        nbits as a signed number (also taking into account that 
        the offset is computed in words, not bytes).
        
        If everyting is successful, the offset is returned.
    """
    if isinstance(arg, Number):
        num = arg.val
        if num_fits_in_nbits(num, nbits, signed=True):
            return num
        else:
            raise InstructionError('Branch offset too large for %d bits' % nbits)
    elif not isinstance(arg, Id):
        raise InstructionError('Invalid branch offset: %s' % arg)

    label = arg.id
    
    if not label in symtab:
        raise InstructionError('Undefined label: %s' % label)
    
    label_addr = symtab[label]
    
    if label_addr[0] != instr_addr[0]:
        raise InstructionError('Branch target in different segment')
    elif label_addr[1] % 4 != 0:
        raise InstructionError('Branch label not aligned at word boundary')
    
    relative_offset = (label_addr[1] - instr_addr[1]) / 4
    
    if not num_fits_in_nbits(relative_offset, nbits, signed=True):
        raise InstructionError('Branch offset too large for %d bits' % nbits)
    
    return relative_offset


# Alias names for registers
#
register_alias = {
    '$zero':    0,
    '$at':      1,
    
    '$v0':      2,
    '$v1':      3,
    
    '$a0':      4,
    '$a1':      5,
    '$a2':      6,
    '$a3':      7,
    
    '$t0':      8,
    '$t1':      9,
    '$t2':      10,
    '$t3':      11,
    '$t4':      12,
    '$t5':      13,
    '$t6':      14,
    '$t7':      15,
    '$t8':      16,
    '$t9':      17,
    
    '$s0':      18,
    '$s1':      19,
    '$s2':      20,
    '$s3':      21,
    '$s4':      22,
    '$s5':      23,
    '$s6':      24,
    '$s7':      25,
    
    '$k0':      26,
    '$k1':      27,
    '$fp':      28,
    
    '$sp':      29,
    '$re':      30,
    '$ra':      31,
}

# Inverted register_alias dictionary for lookup of aliases of 
# register numbers.
#
register_alias_of = dict(zip(register_alias.values(), 
                             register_alias.keys()))


def _reg(arg):
    """ Constructor for register specifiers.
        Expected: Id with id = $r0 .. $r31, or one of the aliases
        for the registers, defined in register_alias.
        
        Returns the numeric representation of the register.
        If an invalid input is given, InstructionError is 
        raised. 
    """
    if isinstance(arg, Id) and arg.id.startswith('$'):
        if arg.id in register_alias:
            return register_alias[arg.id]
        
        m = re.match('\$r(\d\d?)$', arg.id)
        if m and int(m.group(1)) <= 31:
            return int(m.group(1))
        else:
            raise InstructionError('Invalid register: %s' % arg.id)
    else:
        raise InstructionError('Invalid register: %s' % str(arg))


def _const(arg, maxbits=16):
    """ Constructor for numeric constants. 
        Expected: a Number, that is expected to fit into maxbits
        bits. This number can either be signed or unsigned - this
        is to be controlled by the assembly programmer.
        
        Otherwise, InstructionError is raised.
        
        The number is returned as an integer.
    """
    if not (isinstance(arg, Number) and is_int_type(arg.val)):
        raise InstructionError('Invalid number argument: %s' % arg)

    num = arg.val
    
    if (    (num > 0 and num_fits_in_nbits(num, maxbits)) or
            num_fits_in_nbits(num, maxbits, signed=True)):
        return num
    else:
        raise InstructionError("Constant %s won't fit in %s bits" % (num, maxbits))


def _memref(arg, defines):
    """ Constructor for memory reference arguments.
    
        Returns the pair: reg, offset 
    """
    if not isinstance(arg, MemRef):
        raise InstructionError('Invalid memory reference argument: %s' % arg)
    
    reg = _reg(arg.id)
    offset = _define_or_const(arg.offset, defines)
    return reg, offset


def _define_or_const(arg, defines, maxbits=16):
    """ Accepts either numeric constants or constants defined in
        the defines table.
    """
    if isinstance(arg, Id):
        if arg.id in defines:
            return _const(Number(defines[arg.id]), maxbits)
        else:
            raise InstructionError('Undefined constant: %s' % arg.id)
    else:
        return _const(arg, maxbits)


_build_instr_table()

