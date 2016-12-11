# Some utilities for running full tests
#
# Eli Bendersky (C) 2008-2010
#
import os, imp

from lib.commonlib.portability import exec_function
from lib.asmlib.assembler import Assembler
from lib.asmlib.linker import Linker
from lib.commonlib.luz_defs import (
    USER_MEMORY_START, USER_MEMORY_SIZE)


def subdirs(startdir='.', excludes=set()):
    """ Returns an iterator of subdirectories contained in the 
        given one (non-recursively). Full directory path names
        are returned.
    """
    for dir in os.listdir(startdir):
        if not dir in excludes:
            fullpath = os.path.join(startdir, dir)
            if os.path.isdir(fullpath):
                yield fullpath


def get_test_functions(testfile):
    """ Given the path of a testfile, extracts all the test_
        functions from it. Returns an iterator
    """
    module = imp.new_module('test')
    exec_function(open(testfile, 'rU').read(), testfile, module.__dict__)
    
    for attr in dir(module):
        if attr.startswith('test_'):
            yield getattr(module, attr)
    

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

