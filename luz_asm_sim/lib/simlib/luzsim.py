# Main simulator object.
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
#
import struct, sys
import operator

from .memoryunit import MemoryUnit, MemoryError
from .peripheral.errors import PeripheralMemoryError
from .peripheral.coreregisters import CoreRegisters
from .peripheral.debugqueue import DebugQueue
from ..commonlib.utils import (
    extract_bitfield, signed2int, int2signed, num_fits_in_nbits,
    MASK_BYTE, MASK_WORD, MASK_HALFWORD, signed_is_negative,
    unpack_word)
from ..commonlib.luz_opcodes import *
from ..commonlib.luz_defs import (
    USER_MEMORY_START, ExceptionCause, exception_cause_code,
    ADDR_DEBUG_QUEUE)
from ..asmlib.asm_instructions import register_alias


class LuzSim(object):
    """ Public attributes:
    
        pc: 
            The value of the program counter
        halted: 
            A flag specifying whether the CPU is halted (i.e. has
            executed the HALT instruction).
    """
    def __init__(self, image, debug_print=False):
        self.debug_print = debug_print
        self._create_op_map()
        self.restart()
        self.memory = MemoryUnit(image)
        self.memory.register_peripheral_map(
            0, 0xFFF, self.cregs)
        self.memory.register_peripheral_map(
            ADDR_DEBUG_QUEUE, ADDR_DEBUG_QUEUE, self.debugq)
    
    def restart(self):
        self.gpr = [0] * 32
        self.cregs = CoreRegisters()
        self.debugq = DebugQueue(self.debug_print)
        self.pc = USER_MEMORY_START
        self.halted = False
        self.in_exception = False
    
    def step(self):
        try:
            instr = self.memory.read_instruction(self.pc)
            opcode = extract_opcode(instr)
        
            # Dispatch the instruction to a handler
            if opcode in self.op_map:
                self.op_map[opcode](opcode, instr)
            else:
                self._exception_enter(ExceptionCause.INVALID_OPCODE)
            
        except (MemoryError, PeripheralMemoryError):
            self._exception_enter(ExceptionCause.MEMORY_ACCESS)
        except ZeroDivisionError:
            self._exception_enter(ExceptionCause.DIVIDE_BY_ZERO)        

    def run(self):
        while not self.halted:
            self.step()
    
    def reg_value(self, regnum):
        """ The value of the register number 'regnum'
        """
        return self.gpr[regnum]
    
    def reg_alias_value(self, regname):
        """ The value of the register named 'regname' (according
            to the accepted register aliases - $sp, $t0, etc.)
        """
        return self.reg_value(register_alias[regname])
    
    #######################--  PRIVATE --#######################
    
    def _halt_cpu(self):
        self.halted = True
    
    def _exception_enter(self, cause, param=None):
        """ Invoke CPU exception. 
        """
        if self.in_exception:
            self._halt_cpu()
        
        self.in_exception = True
        
        # Save into exception_return_addr the address from which
        # to continue execution when the exception handler 
        # returns.
        # If the instruction invoked an exception, execution must
        # continue from the next instruction. On the other hand,
        # interrupts are entered before the instruction at 'pc'
        # is executed, so we have to come back to it.
        #
        if cause == ExceptionCause.INTERRUPT:
            self.cregs.exception_return_addr.value = self.pc
        else:
            self.cregs.exception_return_addr.value = self.pc + 4
        
        # Set the exception cause
        #
        self.cregs.exception_cause.value = exception_cause_code[cause]
        
        # Jump to the exception handler
        #
        self.pc = self.cregs.exception_vector.value
    
    def _exception_exit(self):
        """ Returns from an exception.
        """
        self.pc = self.cregs.exception_return_addr.value
        self.in_exception = False
    
    def _write_reg(self, regnum, value):
        """ Helper method to write into registers. Makes sure
            that the register number is valid.
            Note: writes into gpr[0] are ignored - it retains its
            zero value.
        """
        if 1 <= regnum <= 31:
            self.gpr[regnum] = value
    
    def _create_op_map(self):
        self.op_map = {
            OP_ADD:     self._op_add_sub,
            OP_SUB:     self._op_add_sub,
            OP_ADDI:    self._op_addi_subi,
            OP_SUBI:    self._op_addi_subi,
            OP_MULU:    self._op_mul,
            OP_MUL:     self._op_mul,
            OP_DIVU:    self._op_div,
            OP_DIV:     self._op_div,
            OP_LUI:     self._op_lui,
            OP_HALT:    self._op_halt,
            OP_ERET:    self._op_eret,
            OP_OR:      self._op_logical_regs,
            OP_AND:     self._op_logical_regs,
            OP_XOR:     self._op_logical_regs,
            OP_NOR:     self._op_logical_regs,
            OP_SLL:     self._op_logical_regs,
            OP_SRL:     self._op_logical_regs,
            OP_ORI:     self._op_logical_imm,
            OP_ANDI:    self._op_logical_imm,
            OP_SLLI:    self._op_logical_imm,
            OP_SRLI:    self._op_logical_imm,
            OP_JR:      self._op_jr,
            OP_CALL:    self._op_call,
            OP_B:       self._op_b,
            OP_BEQ:     self._op_branch_cond,
            OP_BNE:     self._op_branch_cond,
            OP_BGE:     self._op_branch_cond,
            OP_BLE:     self._op_branch_cond,
            OP_BLT:     self._op_branch_cond,
            OP_BGT:     self._op_branch_cond,
            OP_BGEU:    self._op_branch_cond,
            OP_BLEU:    self._op_branch_cond,
            OP_BLTU:    self._op_branch_cond,
            OP_BGTU:    self._op_branch_cond,
            OP_LB:      self._op_load_byte,
            OP_LBU:     self._op_load_byte,
            OP_LH:      self._op_load_halfword,
            OP_LHU:     self._op_load_halfword,
            OP_LW:      self._op_load_word,
            OP_SB:      self._op_store,
            OP_SH:      self._op_store,
            OP_SW:      self._op_store,
        }
    
    #
    # The following methods help accessing the arguments of 
    # instructions.
    #
    
    def _args_3reg(self, instr):
        """ 3-register 
        """
        rd = extract_bitfield(instr, 25, 21)
        rs = extract_bitfield(instr, 20, 16)
        rt = extract_bitfield(instr, 15, 11)
        return rd, rs, rt

    def _args_2reg_imm(self, instr):
        """ 2-register and immediate
        """
        rd = extract_bitfield(instr, 25, 21)
        rs = extract_bitfield(instr, 20, 16)
        imm = extract_bitfield(instr, 15, 0)
        return rd, rs, imm
    
    def _args_1reg_imm16(self, instr):
        """ 1-register and 16-bit immediate
        """
        rd = extract_bitfield(instr, 25, 21)
        imm = extract_bitfield(instr, 15, 0)
        return rd, imm
    
    def _args_1reg(self, instr):
        """ 1-register
        """
        rd = extract_bitfield(instr, 25, 21)
        return rd

    def _args_imm26(self, instr):
        """ 26-bit immediate
        """
        imm = extract_bitfield(instr, 25, 0)
        return imm
    
    def _args_load_reg_address(self, instr):
        """ For load instructions, returns 'rd' and the load
            address.
        """
        rd, rs, offset = self._args_2reg_imm(instr)
        
        # Offset is stored as 2s complement. Turn it into a normal
        # Python integer.
        # Then compute the final load address.
        #
        int_offset = signed2int(offset, nbits=16)
        address = self.gpr[rs] + int_offset
        
        return rd, address
    
    def _args_store_reg_address(self, instr):
        """ For store instructions, returns 'rs' and the store
            address.
        """
        # works similarly to _args_load_reg_address, except that
        # the offset is added to rd, not rs
        #
        rd, rs, offset = self._args_2reg_imm(instr)
        int_offset = signed2int(offset, nbits=16)
        address = self.gpr[rd] + int_offset
        return rs, address

    #
    # The following methods implement the actual CPU instructions
    # 

    def _op_add_sub(self, op, instr):
        rd, rs, rt = self._args_3reg(instr)
        
        if op == OP_ADD:
            val = self.gpr[rs] + self.gpr[rt]
        else: # OP_SUB
            val = self.gpr[rs] - self.gpr[rt]
        
        self._write_reg(rd, val & MASK_WORD)
        self.pc += 4

    def _op_addi_subi(self, op, instr):
        rd, rs, imm = self._args_2reg_imm(instr)

        if op == OP_ADDI:
            val = self.gpr[rs] + imm
        else: # OP_SUBI
            val = self.gpr[rs] - imm
        
        self._write_reg(rd, val & MASK_WORD)
        self.pc += 4

    def _op_mul(self, op, instr):
        rd, rs, rt = self._args_3reg(instr)
        
        if op == OP_MULU:
            val = self.gpr[rs] * self.gpr[rt]
            self._write_reg(rd, val & MASK_WORD)
            self._write_reg(rd + 1, (val >> 32) & MASK_WORD)
        else: # OP_MUL
            val = signed2int(self.gpr[rs]) * signed2int(self.gpr[rt])
            
            if num_fits_in_nbits(val, 32, signed=True):
                self._write_reg(rd, int2signed(val))
            else:                
                # pack as a 8-byte signed value
                packed = struct.pack('<q', val)
                self._write_reg(rd, unpack_word(packed[0:4]))
                self._write_reg(rd + 1, unpack_word(packed[4:8]))

        self.pc += 4

    def _op_div(self, op, instr):
        rd, rs, rt = self._args_3reg(instr)
        
        if op == OP_DIVU:
            quot, rem = divmod(self.gpr[rs], self.gpr[rt])
            self._write_reg(rd, quot)
            self._write_reg(rd + 1, rem)
        else: # OP_DIV
            quot, rem = divmod( signed2int(self.gpr[rs]),
                                signed2int(self.gpr[rt]))
            self._write_reg(rd, int2signed(quot))
            self._write_reg(rd + 1, int2signed(rem))
        
        self.pc += 4

    def _op_lui(self, op, instr):
        rd, imm = self._args_1reg_imm16(instr)
        val = imm << 16
        self._write_reg(rd, val)
        self.pc += 4

    def _op_logical_regs(self, op, instr):
        rd, rs, rt = self._args_3reg(instr)
        
        if op == OP_SRL:
            val = self.gpr[rs] >> (self.gpr[rt] & 0x1F)
        elif op == OP_SLL:
            val = self.gpr[rs] << (self.gpr[rt] & 0x1F)
        elif op == OP_AND:
            val = self.gpr[rs] & self.gpr[rt]
        elif op == OP_OR:
            val = self.gpr[rs] | self.gpr[rt]
        elif op == OP_NOR:
            val = ~(self.gpr[rs] | self.gpr[rt])
        elif op == OP_XOR:
            val = self.gpr[rs] ^ self.gpr[rt]
        else:
            assert False, 'unexpected opcode %s' % op

        self._write_reg(rd, val & MASK_WORD)
        self.pc += 4

    def _op_logical_imm(self, op, instr):
        rd, rs, imm = self._args_2reg_imm(instr)
        
        if op == OP_ORI:
            val = self.gpr[rs] | (imm & MASK_HALFWORD)
        elif op == OP_ANDI:
            val = self.gpr[rs] & (imm & MASK_HALFWORD)
        elif op == OP_SLLI:
            val = self.gpr[rs] << (imm & 0x1F)
        elif op == OP_SRLI:
            val = self.gpr[rs] >> (imm & 0x1F)            
        else:
            assert False, 'unexpected opcode %s' % op
        
        self._write_reg(rd, val & MASK_WORD)
        self.pc += 4

    def _op_jr(self, op, instr):
        rd = self._args_1reg(instr)
        self.pc = self.gpr[rd]

    def _op_call(self, op, instr):
        imm = self._args_imm26(instr)
        
        self._write_reg(31, self.pc + 4)
        self.pc = (imm * 4) & MASK_WORD

    def _op_b(self, op, instr):
        offset = self._args_imm26(instr)
        self.pc += 4 * signed2int(offset, 26)

    # helper table for _op_branch_cond
    # for each conditional branch opcode, holds a pair:
    # (cmp_op, signed_cmp) - see comments in _op_branch_cond for
    # an explanation
    #
    _branch_op_table = {
        OP_BEQ:     (operator.eq, False),
        OP_BNE:     (operator.ne, False),
        OP_BGT:     (operator.gt, True),
        OP_BGTU:    (operator.gt, False),
        OP_BGE:     (operator.ge, True),
        OP_BGEU:    (operator.ge, False),
        OP_BLT:     (operator.lt, True),
        OP_BLTU:    (operator.lt, False),
        OP_BLE:     (operator.le, True),
        OP_BLEU:    (operator.le, False),
    }

    def _op_branch_cond(self, op, instr):
        rd, rs, offset = self._args_2reg_imm(instr)

        # cmp_op: 
        #   The comparison operator - a function taking two 
        #   arguments and returning the boolean result of the 
        #   comparison.
        # signed_cmp:
        #   Should the comparison arguments be treated as signed?
        #
        cmp_op, signed_cmp = self._branch_op_table[op]
        
        if signed_cmp:
            a = signed2int(self.gpr[rd])
            b = signed2int(self.gpr[rs])
        else:
            a, b = self.gpr[rd], self.gpr[rs]
        
        if cmp_op(a, b):
            self.pc += 4 * signed2int(offset, 16)
        else:
            self.pc += 4

    def _op_load_byte(self, op, instr):
        rd, address = self._args_load_reg_address(instr)
        
        # Read the data byte from memory
        #
        data = self.memory.read_mem(address, width=1)
        assert data < 2**8
        
        # For OP_LB and negative data, sign extension is required.
        # Otherwise the data is just copied into the register
        # (zero extension).
        #
        if op == OP_LB and signed_is_negative(data, nbits=8):
            self.gpr[rd] = 0xFFFFFF00 | data
        else:
            self.gpr[rd] = data
        
        self.pc += 4
    
    def _op_load_halfword(self, op, instr):
        # same as _op_load_byte
        rd, address = self._args_load_reg_address(instr)
        data = self.memory.read_mem(address, width=2)
        assert data < 2**16
        
        if op == OP_LH and signed_is_negative(data, nbits=16):
            self.gpr[rd] = 0xFFFF0000 | data
        else:
            self.gpr[rd] = data
            
        self.pc += 4

    def _op_load_word(self, op, instr):
        rd, address = self._args_load_reg_address(instr)
        self.gpr[rd] = self.memory.read_mem(address, width=4)
        self.pc += 4    

    def _op_store(self, op, instr):
        rs, address = self._args_store_reg_address(instr)
        
        if op == OP_SB:
            mask, width = MASK_BYTE, 1
        elif op == OP_SH:
            mask, width = MASK_HALFWORD, 2
        elif op == OP_SW:
            mask, width = MASK_WORD, 4
        else:
            assert False
        
        data = self.gpr[rs] & mask
        
        self.memory.write_mem(address, width, data)
        self.pc += 4

    def _op_eret(self, op, instr):
        self._exception_exit()

    def _op_halt(self, op, instr):
        self._halt_cpu()


