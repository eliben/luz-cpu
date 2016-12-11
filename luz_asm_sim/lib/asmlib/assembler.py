# Assembler - main class
#
# Input: a single assembly source file
# Output: an object file with the assembled source and other
# linkage information (relocation table, list of unresolved
# and exported labels).
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
import pprint, os, sys
from collections import defaultdict

from ..commonlib.utils import (
    word2bytes, num_fits_in_nbits,
    unpack_bytes)

from .asmparser import (
    AsmParser, Instruction, Directive, Id, Number, String)

from .asm_common_types import (
    SegAddr, ExportEntry, ImportEntry, RelocEntry)

from .asm_instructions import (
    InstructionError, instruction_exists, instruction_length,
    assemble_instruction)

from .objectfile import ObjectFile


class ArgumentError(Exception): pass
class AssemblyError(Exception): pass


class Assembler(object):
    def __init__(self):
        self.parser = AsmParser()

    def assemble(self, str=None, filename=None):
        """ Assembles the code given in a string or a file.
            Returns an ObjectFile instance with the results of the
            assembly process.
        
            Provide the code as a string in str. If str is None
            the code is assumed to reside in a file named by
            filename.
        """
        if str is None:
            if filename is None:
                raise ArgumentError('provide str or filename')
            with open(filename, 'rU') as file:
                str = file.read()

        # 1. Parse assembly code into an intermediate format
        #
        imf = self._parse(str)
        
        # 2. First pass
        #
        symtab, addr_imf = self._compute_addresses(imf)
        
        # 3. Second pass
        #
        return self._assemble_code(symtab, addr_imf)

    ######################--   PRIVATE   --######################
    
    def _parse(self, str):
        return self.parser.parse(str)
    
    def _compute_addresses(self, imf):
        """ First pass of the assembler.
            Takes an intermediate form representation of the 
            parsed assembly code (imf).
            
            Builds a symbol table mapping labels defined in the
            code into addresses. The symbol table maps labels
            to SegAddr objects.
            
            Returns a pair: symbol table and an addressed IMF,
            a list of (addr, imf_line) pairs, with addr being the
            address into which the line is to be assembled.
            Note: .segment directives are removed from this list,
            since after the first pass they're no longer required.
            
            Does the minimal amount of work to infer the address
            of each label:
            
            * Recognizes directives and takes into account those
              that allocate storage, and those that specify 
              segments
            * Recognizes instructions and takes into account their 
              lengths
            
            Therefore, the error checking performed here is only
            of the constructs required for construction the symbol
            table:
            
            * Recognition of unknown instructions
            * Validation of only those directives that affect
              address computations.
            * Duplicated label definitions
            * The arguments of directives like .word and .byte
              are not fully verified, but only counted.
        """
        # Symbol table
        # Maps label names to SegAddr objects
        #
        symtab = {}     
        
        # Addressed imf
        # Stores pairs (seg_addr, imf_line) for each line in the
        # intermediate form. seg_addr is a SegAddr object
        #
        addr_imf = []   
        
        # Stores the current address for each segment. All start
        # at 0 when the segment is first defined.
        #
        seg_addr = {}
        
        # The current segment
        #
        cur_seg = None
        
        for line in imf:
            # If there's no "current segment", this line can only
            # be a .segment definition (unlabeled, because this
            # label can have no segment to reference, yet)
            #
            if not cur_seg:
                if not (isinstance(line, Directive) and
                        line.name == '.segment' and
                        not line.label):
                    self._no_segment_error(line.lineno)
            else:
                # Current segment and its running address
                saddr = SegAddr(cur_seg, seg_addr[cur_seg])
            
            # If there's a label, make sure it's not duplicated
            # and add it to the symbol table
            #
            if line.label:
                if line.label in symtab:
                    self._assembly_error("label '%s' duplicated" % line.label, line.lineno)
                
                symtab[line.label] = saddr

            if isinstance(line, Instruction):
                if line.name is None:
                    # Labels without instructions don't affect
                    # the address
                    # They don't have to be added to addr_imf 
                    # either
                    #
                    pass
                elif instruction_exists(line.name):
                    addr_imf.append((saddr, line))
                    seg_addr[cur_seg] += instruction_length(line.name)
                else:
                    self._assembly_error("unknown instruction '%s'" % line.name, line.lineno)
            elif isinstance(line, Directive):
                if cur_seg and line.name != '.segment':
                    addr_imf.append((saddr, line))
                
                if line.name == '.segment':
                    # Switch to the segment named in the 
                    # directive. If it's a new segment, its 
                    # address count starts at 0.
                    #
                    self._validate_args(line, [Id])                    
                    cur_seg = line.args[0].id
                    if not cur_seg in seg_addr:
                        seg_addr[cur_seg] = 0
                elif line.name == '.word':
                    nargs = len(line.args)
                    seg_addr[cur_seg] += nargs * 4
                elif line.name == '.byte':
                    nargs = len(line.args)
                    addr = seg_addr[cur_seg] + nargs
                    seg_addr[cur_seg] = self._align_at_next_word(addr)
                elif line.name == '.alloc':
                    self._validate_args(line, [Number])
                    addr = seg_addr[cur_seg] + int(line.args[0].val)
                    seg_addr[cur_seg] = self._align_at_next_word(addr)
                elif line.name == '.string':
                    self._validate_args(line, [String])
                    # +1 for the zero termination that will be 
                    # inserted when the string is allocated in 
                    # the second pass
                    #
                    addr = seg_addr[cur_seg] + len(line.args[0].val) + 1
                    seg_addr[cur_seg] = self._align_at_next_word(addr)
            else:
                self._assembly_error("bad assembly", line.lineno)
        
        return symtab, addr_imf
    
    def _assemble_code(self, symtab, addr_imf):
        """ Second pass of the assembler. 
            Utilizes the symbol table and the addressed IMF lines
            pre-computed in the first pass to assemble the code
            into object data.
        """
        # Holds constants defined with the .define directive
        #
        defines = {}
        
        # The assembled data as a list of bytes, per segment
        #
        seg_data = defaultdict(list)
        
        export_table = []
        import_table = []
        reloc_table = []
        
        # addr: a SegAddr object
        # line: the parsed IMF for a line of assembly
        #
        for addr, line in addr_imf:
            if isinstance(line, Instruction):
                # Sanity check: are we shoving the instruction(s)
                # in the right place?
                #
                assert len(seg_data[addr.segment]) == addr.offset
                
                # Assemble the instruction. This returns a list
                # of AssembledInstruction objects.
                #
                try:
                    asm_instrs = assemble_instruction(
                        line.name, line.args, addr, 
                        symtab, defines)
                except InstructionError:
                    err = sys.exc_info()[1]
                    self._assembly_error(err, line.lineno)
                
                for asm_instr in asm_instrs:
                    # The offset in the segment this instruction
                    # will be placed into
                    #
                    offset = len(seg_data[addr.segment])
                    
                    if asm_instr.import_req:
                        type, symbol = asm_instr.import_req
                        # note that we're using offset, and not
                        # addr.offset here, because this could be
                        # a pseudo-instruction assembling to two
                        # instructions, and addr.offset points 
                        # only to the first one.
                        #
                        import_table.append(ImportEntry(
                            import_symbol=symbol,
                            type=type,
                            addr=SegAddr(addr.segment, offset)))                    
                    
                    if asm_instr.reloc_req:
                        type, segment = asm_instr.reloc_req
                        reloc_table.append(RelocEntry(
                            reloc_segment=segment,
                            type=type,
                            addr=SegAddr(addr.segment, offset)))
                    
                    # Add the assembled instruction into the 
                    # segment data
                    #
                    seg_data[addr.segment].extend(word2bytes(asm_instr.op))
            elif isinstance(line, Directive):
                if line.name == '.define':
                    # Add the defined symbol to the defines table,
                    # possibly overriding a previous definition
                    #
                    self._validate_args(line, [Id, Number])                    
                    defines[line.args[0].id] = line.args[1].val
                elif line.name == '.global':
                    self._validate_args(line, [Id])
                    symbol_name = line.args[0].id
                    
                    # The exported symbol must be present in the
                    # symbol table collected by the first pass
                    #
                    if symbol_name in symtab:
                        export_table.append(ExportEntry(
                            export_symbol=symbol_name,
                            addr=symtab[symbol_name]))
                    else:
                        self._assembly_error('.global defines an unknown label %s' % symbol_name, line.lineno)
                elif line.name == '.alloc':
                    # The arguments of .alloc directives were 
                    # validated in the first pass
                    #
                    num = self._align_at_next_word(line.args[0].val)
                    seg_data[addr.segment].extend([0] * num)
                elif line.name == '.byte':
                    data = []
                    
                    for i, byte_arg in enumerate(line.args):
                        if (isinstance(byte_arg, Number) and
                            num_fits_in_nbits(byte_arg.val, 8)
                            ):
                            data.append(byte_arg.val)
                        else:
                            self._assembly_error('.byte -- argument %s not a valid byte' % (i + 1,), line.lineno)
                 
                    leftover = len(data) % 4
                    if leftover:
                        data.extend([0] * (4 - leftover))
                    
                    seg_data[addr.segment].extend(data)
                elif line.name == '.word':
                    data = []
                    
                    for i, word_arg in enumerate(line.args):
                        if (isinstance(word_arg, Number) and
                            num_fits_in_nbits(word_arg.val, 32)
                            ):
                            data.extend(word2bytes(word_arg.val))
                        else:
                            self._assembly_error('.word -- argument %s not a valid word' % (i + 1,), line.lineno)
                    
                    seg_data[addr.segment].extend(data)
                elif line.name == '.string':
                    data = unpack_bytes(line.args[0].val + '\x00')
                    leftover = len(data) % 4
                    if leftover:
                        data.extend([0] * (4 - leftover))
                    
                    seg_data[addr.segment].extend(data)
                else:
                    # .segment directives should not be passed
                    # here by the first pass
                    #
                    if line.name == '.segment':
                        assert 0
                        
                    self._assembly_error('unknown directive %s' % line.name, line.lineno)
            else:
                self._assembly_error("bad assembly", line.lineno)

        return ObjectFile.from_assembler(
                    seg_data=seg_data, 
                    export_table=export_table, 
                    import_table=import_table, 
                    reloc_table=reloc_table)
    
    def _validate_args(self, line, exp_args):
        """ Validates that the arguments of the 
            directive stored in 'line' are of the correct amount 
            and types.
        """
        if len(exp_args) != len(line.args):
            self._assembly_error("%s -- %s argument(s) expected" % (line.name, len(exp_args)), line.lineno)

        for i, exp_type in enumerate(exp_args):
            if not isinstance(line.args[i], exp_type):
                self._assembly_error("%s -- argument '%s' of unexpected type" % (line.name, line.args[i]), line.lineno)
    
    def _no_segment_error(self, lineno):
        self._assembly_error("A segment must be defined before this line", lineno)
    
    def _assembly_error(self, msg, lineno):
       raise AssemblyError("%s (at line %s)" % (msg, lineno))
    
    def _align_at_next_word(self, addr):
        """ Make sure an address is aligned at a word (4-byte) 
            boundary. If it isn't, align it at the next word.
        """
        offset = addr % 4;
        if offset == 0:
            return addr
        else:
            return addr + (4 - offset)

