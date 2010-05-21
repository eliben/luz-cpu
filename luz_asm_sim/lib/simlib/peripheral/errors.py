# Error classes for peripherals
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
#

class PeripheralError(Exception): pass
class PeripheralMemoryError(Exception): pass
class PeripheralMemoryAlignError(PeripheralMemoryError): pass
class PeripheralMemoryAccessError(PeripheralMemoryError): pass


