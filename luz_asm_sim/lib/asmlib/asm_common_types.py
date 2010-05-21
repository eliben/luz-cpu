# Common types used by various parts of the assembler and linker.
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#

from collections import namedtuple
from ..commonlib.utils import Enum


# Used to carry around (segment, offset) pairs, since each address
# in the assembler is an offset inside some segment.
#
SegAddr = namedtuple('SegAddr', 'segment offset')


# An export entry consists of:
#   export_symbol:
#       The name of the exported symbol
#   addr:
#       The address represented by this symbol (SegAddr) in the
#       object file.
#
ExportEntry = namedtuple(   'ExportEntry',
                            'export_symbol addr')

# An import entry consists of:
#   import_symbol:
#       The name of the symbol required for importing. Its updated 
#       address is inserted at the referring instruction.
#   type:
#       Tells the linker how to insert the symbol address.
#   addr:
#       Address of the referring instruction (SegAddr) - where the 
#       symbol's address will be inserted.
#
ImportType = Enum('CALL', 'LI')
ImportEntry = namedtuple(   'ImportEntry', 
                            'import_symbol type addr')


# A relocation entry consists of:
#   reloc_segment:
#       The name of the segment required for relocation. Its 
#       updated address is inserted at the referring instruction.
#   type:
#       Tells the linker how to insert the segment address.
#   addr:
#       Address of the referring instruction (SegAddr) - where the 
#       segment's address will be inserted.
#
RelocType = Enum('CALL', 'LI')
RelocEntry = namedtuple(    'RelocEntry',
                            'reloc_segment type addr')


