# Op-codes of Luz instructions. 
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#

from .utils import extract_bitfield


def extract_opcode(instr):
    return extract_bitfield(instr, 31, 26)


# All the opcodes in numeric order
#
OP_ADD      = 0x00
OP_SUB      = 0x01
OP_MULU     = 0x02
OP_MUL      = 0x03
OP_DIVU     = 0x04
OP_DIV      = 0x05
OP_LUI      = 0x06
OP_SLL      = 0x07
OP_SRL      = 0x08
OP_AND      = 0x09
OP_OR       = 0x0A
OP_NOR      = 0x0B
OP_XOR      = 0x0C
OP_LB       = 0x0D
OP_LH       = 0x0E
OP_LW       = 0x0F
OP_LBU      = 0x10
OP_LHU      = 0x11
OP_SB       = 0x12
OP_SH       = 0x13
OP_SW       = 0x14
OP_B        = 0x15
OP_JR       = 0x16
OP_BEQ      = 0x17
OP_BNE      = 0x18
OP_BGE      = 0x19
OP_BGT      = 0x1A
OP_BLE      = 0x1B
OP_BLT      = 0x1C
OP_CALL     = 0x1D
OP_ADDI     = 0x20
OP_SUBI     = 0x21
OP_BGEU     = 0x22
OP_BGTU     = 0x23
OP_BLEU     = 0x24
OP_BLTU     = 0x25
OP_ANDI     = 0x29
OP_ORI      = 0x2A
OP_SLLI     = 0x2B
OP_SRLI     = 0x2C
OP_ERET     = 0x3E
OP_HALT     = 0x3F
