# Generic memory-mapped peripheral interface.
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
#

class Peripheral(object):
    """ An abstract memory-mapped perhipheral interface.
        Memory-mapped peripherals are accessed through memory
        reads and writes.

        The address given to reads and writes is relative to the
        peripheral's memory map.
        Width is 1, 2, 4 for byte, halfword and word accesses.
    """
    def read_mem(self, addr, width):
        raise NotImplementedError()

    def write_mem(self, addr, width, data):
        raise NotImplementedError()
