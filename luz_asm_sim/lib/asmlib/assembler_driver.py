# "Driver" routines for assembling a bunch of .lasm files into a .hex binary
# image.
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
from .assembler import Assembler
from .linker import Linker
from ..commonlib.luz_defs import (
    USER_MEMORY_START, USER_MEMORY_SIZE)
from ..commonlib.binaryappdata import (
    BinaryAppDataStore, DataFormatterIntelHex)
from ..commonlib.utils import pack_bytes


def link_asmfiles(asmfiles):
    """ Given a list of assembly files, assembles and links them
        and returns the executable image.
    """
    # assemble all the .lasm files
    asm = Assembler()
    objs = [asm.assemble(filename=f) for f in asmfiles]
    
    # link into a binary image
    link = Linker(USER_MEMORY_START, USER_MEMORY_SIZE)
    img = link.link(objs)

    return img


def assemble_binary(
        asmfiles,                   # List of .lasm file names
        output='image.hex',         # Ouput file name
        ulba=0,                     # Upper Linear Base Address for output file
    ):
    # Assemble and link all input files into a binary image
    #
    image_str = pack_bytes(link_asmfiles(asmfiles))
    
    # Write the image to the output file in Intel HEX format
    #
    datastore = BinaryAppDataStore()
    datastore.add_record(ulba, image_str)
    intel_formatter = DataFormatterIntelHex(datastore)
    intel_formatter.write(filename=output)

