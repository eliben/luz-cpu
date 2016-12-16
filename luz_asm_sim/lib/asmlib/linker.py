# Linker - the linker for assembled objects
#
# Input: one or more ObjectFile objects
# Output: an executable suitable for loading into the Luz
# simulator or CPU memory.
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
import pprint, os, sys, string
from collections import defaultdict

from ..commonlib.utils import (
                    word2bytes, bytes2word, extract_bitfield,
                    build_bitfield, num_fits_in_nbits)
from ..commonlib.luz_opcodes import *
from .asm_common_types import ImportType, RelocType
from .assembler import Assembler

class LinkerError(Exception): pass


class Linker(object):
    """ Links together several object files, adding a startup
        object, and produces a binary image of the linked
        executable. This binary image, when loaded at the initial
        offset address, is ready to be executed by the CPU.

        A Linker is created with the following parameters:

        initial_offset:
            The initial offset in memory where the image will be
            placed. This is important for resolving relocations
            and imports.

        mem_size:
            The total memory size available for the executable.
            This is used to initialize the stack pointer.

        Calling the link() method results in the binary image as
        a list of bytes.
    """
    def __init__(self, initial_offset=0, mem_size=128*1024):
        self.initial_offset = initial_offset
        self.mem_size = mem_size

        self.startup_object = self._assemble_startup_code()

    def link(self, object_files=[]):
        """ Link the given objects. object_files is a list of
            ObjectFile. The objects are linked with the special
            startup object (see LINKER_STARTUP_CODE).

            Note: object files may be modified as a result of this
            call, to resolve import and relocations.
        """
        # Throughout the linking code we refer to objects
        # by their offset in the object_files list. This offset
        # uniquely identifies an object.
        #
        self.object_files = object_files
        startup_object = self._assemble_startup_code()
        self.object_files.append(startup_object)

        segment_map, total_size = self._compute_segment_map(
            object_files=self.object_files,
            offset=self.initial_offset)

        exports = self._collect_exports(
            object_files=self.object_files)

        self._resolve_imports(
            object_files=self.object_files,
            exports=exports,
            segment_map=segment_map)

        self._resolve_relocations(
            object_files=self.object_files,
            segment_map=segment_map)

        image = self._build_memory_image(
            object_files=self.object_files,
            segment_map=segment_map,
            total_size=total_size)

        return image

    ######################--   PRIVATE   --#####################

    def _assemble_startup_code(self):
        sp_ptr = self.initial_offset + self.mem_size - 4
        startup_code = LINKER_STARTUP_CODE.substitute(
            SP_POINTER=sp_ptr)

        asm = Assembler()
        startup_object = asm.assemble(str=startup_code)
        return startup_object

    def _compute_segment_map(self, object_files, offset=0):
        """ Compute a segment memory map from the list of object
            files and a given offset.

            A "segment map" is a list of:
                dict[segment] = address

            The ith item holds such a dictionary for the ith
            object file.
            Each dictionary maps the segments found in this
            object file into the addresses to which they are
            placed in the memory layout created by the linker.

            For example, if several objects have a 'text' segment,
            this function collects all the 'text' segments into
            a contiguous region. However, the 'text' segment of
            each object will point to a different offset inside
            this region (since they're placed one after another).

            The 'offset' argument allows to shift the whole memory
            map by some constant amount.

            Linker-created segments like __startup and __heap are
            treated specially.

            Returns the pair segment_map, total_size
            total_size is the total size of memory occupied by
            all the objects.
        """
        # Step 1: Compute the total sizes of all segments that
        # exist in the object files
        #
        segment_size = defaultdict(int)
        for obj in object_files:
            for segment in obj.seg_data:
                segment_size[segment] += len(obj.seg_data[segment])

        # Step 2: Initialize the pointers that point to the start
        # of each combined segment.
        # Note: the order of allocation of segments (what comes
        # after what) isn't really important and could be totally
        # arbitrary. To make it more predictable, segments are
        # allocated one after another sorted by name in increasing
        # lexicographical order.
        # The __startup segment is placed before all others (i.e.
        # it's mapped at 'offset'), and the __heap segment is
        # placed after all others.
        #
        segment_ptr = {}
        ptr = offset

        if '__startup' in segment_size:
            segment_ptr['__startup'] = ptr
            ptr += segment_size['__startup']

        for segment in sorted(segment_size):
            if segment not in ('__startup', '__heap'):
                segment_ptr[segment] = ptr
                ptr += segment_size[segment]

        if '__heap' in segment_size:
            segment_ptr['__heap'] = ptr
            ptr += segment_size['__heap']

        total_size = ptr - offset

        # Step 3: Create the segment map. For each segment in each
        # object, record the memory offset where it will be
        # mapped.
        #
        segment_map = []
        for obj in object_files:
            obj_segment_map = {}
            for segment in obj.seg_data:
                obj_segment_map[segment] = segment_ptr[segment]
                segment_ptr[segment] += len(obj.seg_data[segment])
            segment_map.append(obj_segment_map)

        return segment_map, total_size

    def _collect_exports(self, object_files):
        """ Collects the exported symbols from all the objects.
            Verifies that exported symbols are unique and
            notifies of collisions.

            The returned data structure is a dict mapping export
            symbol names to a pair: (object_index, addr)
            where object_index is the index in object_files of the
            object that exports this symbol, and addr is
            the address of the symbol (SegAddr) taken from the
            export table of that object.
        """
        exports = {}

        for idx, obj in enumerate(object_files):
            for export in obj.export_table:
                sym_name = export.export_symbol
                if sym_name in exports:
                    other_idx = exports[sym_name][0]
                    self._linker_error(
                        "Duplicated export symbol '%s' at objects [%s] and [%s]" % (
                            sym_name,
                            self._object_id(object_files[idx]),
                            self._object_id(object_files[other_idx])))

                exports[sym_name] = (idx, export.addr)

        return exports

    def _resolve_relocations(self, object_files, segment_map):
        """ Resolves the relocations in object files according to
            their relocation tables and the updated segment_map
            information.
        """
        # Look at the relocation tables of all objects
        #
        for idx, obj in enumerate(object_files):
            for reloc_seg, type, addr in obj.reloc_table:
                # The requested relocation segment should exist
                # in the segment map for this object.
                #
                if not reloc_seg in segment_map[idx]:
                    self._linker_error("Relocation entry in object [%t] refers to unknown segment %s" % (
                        self._object_id(obj), reloc_seg))

                # This is where the relocated segment was mapped
                #
                mapped_address = segment_map[idx][reloc_seg]

                # Patch the instruction asking for relocation with
                # the mapped address of the requested segment.
                #
                self._patch_segment_data(
                    seg_data=obj.seg_data[addr.segment],
                    instr_offset=addr.offset,
                    type=type,
                    mapped_address=mapped_address,
                    name=reloc_seg)

    def _resolve_imports(self, object_files, segment_map, exports):
        """ Resolves the imports in object files according to the
            exported symbols collected in exports and the mapping
            of segments into memory (segment_map).
        """
        # Look at the import tables of all objects
        #
        for idx, obj in enumerate(object_files):
            import_table = object_files[idx].import_table

            # All imported symbols
            #
            for sym, import_type, import_addr in import_table:
                # Make sure this symbol was indeed exported by
                # some object
                #
                if not sym in exports:
                    self._linker_error("Failed import of symbol '%s' at object [%s]" % (
                        sym, self._object_id(obj)))
                exp_obj_idx, exp_address = exports[sym]

                # From the export table, build the final mapped
                # address of this symbol.
                # It is the mapped value of the segment in which
                # this symbol is located, plus its offset in that
                # segment.
                #
                mapped_address = segment_map[exp_obj_idx][exp_address.segment]
                mapped_address += exp_address.offset

                # Now patch the segment data of this object.
                # The instruction(s) to patch and the patch type
                # are taken from the import table, and the address
                # to insert is the mapped_address computed from
                # the matching exported symbol.
                #
                self._patch_segment_data(
                    seg_data=obj.seg_data[import_addr.segment],
                    instr_offset=import_addr.offset,
                    type=import_type,
                    mapped_address=mapped_address,
                    name=sym)

    def _patch_segment_data(self,
            seg_data,
            instr_offset,
            type,
            mapped_address,
            name='<unknown>'):
        """ Performs a patch of segment data.

            seg_data:
                The segment data of the relevant segment
            instr_offset:
                Offset of the instruction that is to be patched in
                the segment.
            type:
                Patch type (one of types listed in ImportType or
                RelocType)
            mapped_address:
                The address that will be patched into the
                instruction(s).
            name:
                Symbol/segment name used for debugging

            The segment data is modified as a result of this call.
        """
        if instr_offset > len(seg_data) - 4:
            self._linker_error("Patching (%s) of '%s', bad offset into segment" % (
                type, name))

        # At the moment only CALL and LI patches are supported
        #
        patch_call = type in (ImportType.CALL, RelocType.CALL)

        # For import patches, the address stored in the
        # instruction is replaced with the mapped address.
        # For reloc patches, the two addresses are added
        #
        do_replace = type in (ImportType.CALL, ImportType.LI)

        if patch_call:
            orig_instr_bytes = seg_data[instr_offset:instr_offset+4]
            orig_instr_word = bytes2word(orig_instr_bytes)

            # Break the instruction into opcode and destination
            # address. Make sure it's indeed a CALL
            #
            opcode = extract_opcode(orig_instr_word)
            if opcode != OP_CALL:
                self._linker_error("Patching (%s) of '%s': expected CALL, got %d" % (
                    type, name, opcode))

            # CALL destinations are in words
            #
            mapped_address //= 4

            # Patch the address
            #
            if do_replace:
                destination = mapped_address
            else:
                destination = extract_bitfield(orig_instr_word, 25, 0)
                destination += mapped_address

            if not num_fits_in_nbits(destination, 26):
                self._linker_error("Patching (%s) of '%s': patched destination address %x too large" % (
                    type, name, destination))

            # Build the new instruction and shove it back into
            # the segment data
            #
            new_instr_bytes = word2bytes(
                build_bitfield(31, 26, opcode) |
                build_bitfield(25, 0, destination))

            seg_data[instr_offset:instr_offset+4] = new_instr_bytes
        else:
            # Patch LI
            # Handled similarly to patching CALL, except that the
            # instructions that replaced LI (LUI followed by ORI)
            # have to be patched.
            #
            orig_bytes = seg_data[instr_offset:instr_offset+8]
            orig_lui_word = bytes2word(orig_bytes[0:4])
            orig_ori_word = bytes2word(orig_bytes[4:8])

            opcode_lui = extract_opcode(orig_lui_word)
            opcode_ori = extract_opcode(orig_ori_word)

            if opcode_lui != OP_LUI and opcode_ori != OP_ORI:
                self._linker_error("Patching (%s) of '%s': expected LI, got %d,%d" % (
                    type, name, opcode_lui, opcode_ori))

            if do_replace:
                destination = mapped_address
            else:
                # Build the original destination address by combining
                # the high and low parts from the two instructions
                #
                destination = extract_bitfield(orig_lui_word, 15, 0) << 16
                destination += extract_bitfield(orig_ori_word, 15, 0)
                destination += mapped_address

            if not num_fits_in_nbits(destination, 32):
                self._linker_error("Patching (%s) of '%s': patched destination address %x too large" % (
                    type, sym_name, destination))

            orig_lui_rd = extract_bitfield(orig_lui_word, 25, 21)
            new_lui_bytes = word2bytes(
                build_bitfield(31, 26, opcode_lui) |
                build_bitfield(25, 21, orig_lui_rd) |
                build_bitfield(15, 0, destination >> 16))

            # in LUI created from LI Rd is in both Rd and Rs
            # fields
            #
            orig_ori_rd = extract_bitfield(orig_ori_word, 25, 21)
            new_ori_bytes = word2bytes(
                build_bitfield(31, 26, opcode_ori) |
                build_bitfield(25, 21, orig_ori_rd) |
                build_bitfield(20, 16, orig_ori_rd) |
                build_bitfield(15, 0, destination & 0xFFFF))

            seg_data[instr_offset:instr_offset+4] = new_lui_bytes
            seg_data[instr_offset+4:instr_offset+8] = new_ori_bytes

    def _build_memory_image(self, object_files, segment_map, total_size):
        """ Builds a linked memory image of the objects mapped
            according to segment map.
            Returns a list of bytes that should be loaded to
            self.initial_offset in the CPU's memory.
        """
        SENTINEL = -999
        image = [SENTINEL] * total_size

        for idx, obj in enumerate(object_files):
            for segment in obj.seg_data:
                seg_data = obj.seg_data[segment]

                start = segment_map[idx][segment] - self.initial_offset
                end = start + len(seg_data)

                # sanity check: the segments don't trample over
                # each other
                #
                for i in range(start, end):
                    assert image[i] == SENTINEL, 'segment %s at %d' % (segment, i)

                image[start:end] = seg_data

        # sanity check: no sentinels left
        #
        for i in range(total_size):
            assert image[i] != SENTINEL, 'at %d' % i
        return image

    def _object_id(self, object_file):
        """ Returns a string identification of the given object
            file. If it has a name, that's returned. Otherwise,
            its id is returned as a string.
        """
        if object_file.name:
            return object_file.name
        else:
            return hex(id(object_file))

    def _linker_error(self, msg):
       raise LinkerError(msg)


# The special segments added by the linker.
# __startup: 3 words
# __heap: 1 word
#
LINKER_STARTUP_CODE = string.Template(r'''
        .segment __startup

    LI      $$sp, ${SP_POINTER}
    CALL    asm_main

        .segment __heap
        .global __heap
    __heap:
        .word 0
''')
