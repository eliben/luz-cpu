# Simulates the CPU control registers
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
#
from .peripheral import Peripheral
from .errors import (PeripheralMemoryAccessError,
    PeripheralMemoryAlignError)
from ...commonlib.utils import MASK_WORD
from ...commonlib.luz_defs import (
    ADDR_EXCEPTION_VECTOR, ADDR_CONTROL_1, ADDR_EXCEPTION_CAUSE,
    ADDR_EXCEPTION_RETURN_ADDR, ADDR_INTERRUPT_ENABLE,
    ADDR_INTERRUPT_PENDING)


# Maps memory addresses of registers to names
#
cregs_memory_map = {
    ADDR_EXCEPTION_VECTOR:      'exception_vector',
    ADDR_CONTROL_1:             'control_1',
    ADDR_EXCEPTION_CAUSE:       'exception_cause',
    ADDR_EXCEPTION_RETURN_ADDR: 'exception_return_addr',
    ADDR_INTERRUPT_ENABLE:      'interrupt_enable',
    ADDR_INTERRUPT_PENDING:     'interrupt_pending',
}


class CoreRegisters(Peripheral):
    """ Simulates the CPU core registers (accessible to the
        program via the memory unit in the core address space).
    """
    class CoreReg(object):
        def __init__(self, value, user_writable):
            self.value = value
            self.user_writable = user_writable
    
    def __init__(self):
        self.exception_vector =         self.CoreReg(0, True)
        self.control_1 =                self.CoreReg(0, True)
        self.exception_cause =          self.CoreReg(0, False)
        self.exception_return_addr =    self.CoreReg(0, False)
        self.interrupt_enable =         self.CoreReg(0, True)
        self.interrupt_pending =        self.CoreReg(0, False)

    def __getitem__(self, name):
        """ Allow accessing registers by name
        """
        return self.__dict__[name]

    def read_mem(self, addr, width):
        if width != 4 or addr % 4 != 0:
            raise PeripheralMemoryAlignError()
        
        if addr in cregs_memory_map:
            creg_name = cregs_memory_map[addr]
            return self[creg_name].value
        else:
            raise PeripheralMemoryAccessError()
        
    def write_mem(self, addr, width, data):
        if width != 4 or addr % 4 != 0:
            raise PeripheralMemoryAlignError()
        
        if addr in cregs_memory_map:
            creg_name = cregs_memory_map[addr]
            if self[creg_name].user_writable:
                self[creg_name].value = data & MASK_WORD
        else:
            raise PeripheralMemoryAccessError()



