# Common definitions for the Luz CPU.
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#

from collections import namedtuple
from .utils import Enum


USER_MEMORY_START = 0x100000
USER_MEMORY_SIZE = 0x40000

ADDR_EXCEPTION_VECTOR       = 0x004
ADDR_CONTROL_1              = 0x100
ADDR_EXCEPTION_CAUSE        = 0x108
ADDR_EXCEPTION_RETURN_ADDR  = 0x10C
ADDR_INTERRUPT_ENABLE       = 0x120
ADDR_INTERRUPT_PENDING      = 0x124

ADDR_DEBUG_QUEUE            = 0xF0000

ExceptionCause = Enum(
    'TRAP', 'DIVIDE_BY_ZERO', 'MEMORY_ACCESS',
    'INVALID_OPCODE', 'INTERRUPT')


exception_cause_code = {
    ExceptionCause.TRAP:                1,
    ExceptionCause.DIVIDE_BY_ZERO:      2,
    ExceptionCause.MEMORY_ACCESS:       3,
    ExceptionCause.INVALID_OPCODE:      4,
    ExceptionCause.INTERRUPT:           32,
}



