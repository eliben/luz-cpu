# Simulates the memory unit of the CPU. Provides memory mapping
# for both the user-memory area and the CPU internal registers
# and peripherals.
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
#

from ..commonlib.luz_defs import (
    USER_MEMORY_START, USER_MEMORY_SIZE)
from ..commonlib.utils import (
    MASK_WORD, MASK_BYTE,
    bytes2word, bytes2halfword, word2bytes, halfword2bytes)
from .peripheral.coreregisters import CoreRegisters

USER_MEMORY_END = USER_MEMORY_START + USER_MEMORY_SIZE


# Error classes
#
class MemoryError(Exception): pass
class MemoryAlignError(MemoryError): pass
class MemoryAccessError(MemoryError): pass


class MemoryUnit(object):
    def __init__(self, user_image):
        self.user_image = user_image
        
        # All addresses mapped to peripherals.
        # Each entry contains a (handler, from_addr) pair.
        # Read and write accesses will be passed to the handler
        # with addresses relative to from_addr.
        #
        self.peripheral_memory_map = {}
        
        if len(self.user_image) < USER_MEMORY_SIZE:
            padding = [0] * (USER_MEMORY_SIZE - len(self.user_image))
            self.user_image.extend(padding)
    
    def register_peripheral_map(self, from_addr, to_addr, handler):
        """ Register a memory mapped peripheral. Accesses to the 
            [from_addr..to_addr] inclusive range will be 
            passed to the handler.
        """
        for addr in range(from_addr, to_addr + 1):
            self.peripheral_memory_map[addr] = handler, from_addr
    
    def read_instruction(self, addr):
        """ Reads an instruction word from the given address.
        
            Exists as a separate method from 'read_mem' for 
            convenience (statistics, consistency checks, etc.)
        """
        self._check_user_memory_access(addr, 4)
        return self._read_word(addr)
    
    def read_mem(self, addr, width):
        """ Read memory at the given address. The width is 
            4, 2, or 1.
        """
        if addr in self.peripheral_memory_map:
            handler, from_addr = self.peripheral_memory_map[addr]
            return handler.read_mem(addr - from_addr, width)
        else: # Assume it's an access to user memory
            self._check_user_memory_access(addr, width)
            
            if width == 4:
                return self._read_word(addr)
            elif width == 2:
                return self._read_halfword(addr)
            else:
                return self._read_byte(addr)
    
    def write_mem(self, addr, width, data):
        """ Write memory at the given address. 
        """
        if addr in self.peripheral_memory_map:
            handler, from_addr = self.peripheral_memory_map[addr]
            handler.write_mem(addr - from_addr, width, data)
        else: # Assume it's an access to user memory
            self._check_user_memory_access(addr, width)
            
            if width == 4:
                self._write_word(addr, data)
            elif width == 2:
                self._write_word(addr, data)
            else:
                self._write_byte(addr, data)            

    ######################## PRIVATE #############################

    def _check_user_memory_access(self, addr, width):
        """ Check that the user memory access of the specified
            width is valid.
        """
        assert width in (1, 2, 4)
        if addr % width != 0:
            raise MemoryAlignError()        
        elif not (USER_MEMORY_START <= addr < USER_MEMORY_END):
            raise MemoryAccessError('address 0x%08X out of bounds' % addr)

    #
    # The following methods all assume that the address they're
    # given is valid and properly aligned.
    #
    def _read_word(self, addr):
        start = addr - USER_MEMORY_START
        return bytes2word(self.user_image[start:start+4])

    def _read_halfword(self, addr):
        start = addr - USER_MEMORY_START
        return bytes2halfword(self.user_image[start:start+2])

    def _read_byte(self, addr):
        return self.user_image[addr - USER_MEMORY_START]

    def _write_word(self, addr, data):
        start = addr - USER_MEMORY_START
        self.user_image[start:start+4] = word2bytes(data)
    
    def _write_halfword(self, addr, data):
        start = addr - USER_MEMORY_START
        self.user_image[start:start+2] = halfword2bytes(data)

    def _write_byte(self, addr, data):
        start = addr - USER_MEMORY_START
        self.user_image[start] = data & MASK_BYTE



