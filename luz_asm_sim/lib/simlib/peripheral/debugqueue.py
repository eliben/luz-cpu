# Simulates a "debug queue" peripheral.
# This peripheral can be written to by the user's program. It 
# saves all the words that were written in a FIFO queue that can
# be accessed by the simulator at any time, for debugging 
# purposes.
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
#
from .peripheral import Peripheral
from ...commonlib.portability import printme


class DebugQueue(Peripheral):
    """ Public attributes:
            
            items:
                A list of words written to the queue in FIFO order
    """
    def __init__(self, debug_print=False):
        self.debug_print = debug_print
        self.reset()
        
    def reset(self):
        self.items = []
    
    def read_mem(self, addr, width):
        """ This peripheral is write-only.
            Reads are ignored.
        """
        pass
    
    def write_mem(self, addr, width, data):
        """ Only the correct address is mapped to this peripheral,
            and we don't care about width...
        """
        self.items.append(data)
        
        if self.debug_print:
            printme('DebugQueue: 0x%X\n' % data)


    

