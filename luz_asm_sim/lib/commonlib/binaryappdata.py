"""
binaryappdata.py - a framework for creating, reading and writing
files in various application binary data formats.

Application binary data files are encountered when creating
embedded software for PROM/Flash programming, or hardware
emulators.

==================== Formats ====================

The formats currently supported by this module are:

Raw binary
==========
Your vanilla binary files - they specify only the memory contents
and no special information like the start address.

Some tools need a whole-image file to initialize the Flash. If the
Flash can hold 32Kbytes, the programming files will be 32KB
binaries.

Hexpair ASCII
=============
45 A3 FF FF FF FF 55 AA DE AD BE EF

These are equivalent to binary files semantically, but coded in
plain-text ASCII. Hexadecimal pairs denote bytes. For example,
the 'hexpair' representation of 'abc' is '61 62 63'.

The input hex digits can be either lower or upper case (this
applies to A-F, of course), and the pairs can be separated by any
characters that are not valid hex digits (0-9a-fA-F), or not
separated at all (i.e. 'aa55' is treated the same way as 'aa, 55'
Naturally, it's more prudent to separate the data with punctuation
and/or whitespace, and not alphabetic characters.

When separators are used, a hexpair file takes up roughly 3 times
as much space as a plain binary file with the same contents.
Without separators, the ratio is 2:1

Intel HEX
=========
A more sophisticated ASCII-based format, widely used by several
vendors. This module fully complies with the document named
"Intel Hexadecimal Object File Format Specification Revision A",
which you can freely obtain online (just Google it).

==================== Examples ====================

Some examples of usage can be found in tests/example_tests.py
They should cover 99% of the use-cases for this module, so please
read them !
The examples are built as unit-tests, to both demonstrate how the
module is really used and to make sure they actually work (don't
you just hate examples that aren't up-to-date with the code...)

================ API Documentation ===============

The recommended starting point to undertand binaryappdata is the
examples. Once you've seen the examples, you can read the
extensive docstrings of the various classes in this module.

A couple of general notes about the design:

binaryappdata is built as a family of related classes for maximal
flexibility. How you use it depends on what you need to do.

* If you just need to convert from one file format to another,
  using the DataFormatter classes will be enough. These classes
  know how to handle all the formats supported by binaryappdata.
* To create and store, or load and manipulate binary data, you'll
  have to work with BinaryAppDataStore as well. This is a generic,
  format-agnostic 'store' of binary application data.
* To handle other formats, you can just implement another
  DataFormatter class. Drop me an email though, perhaps I'd like
  to add it to the distribution.

BinaryAppDataStore is built around the concept of 'records'. Each
record is a consecutive chunk of data residing at some address.
It is useful to speak of records, because binary application files
(chiefly Intel HEX and Motorola S-Record) are built from such
chunks (for example, the text and data segments are different
chunks that may reside in different memory areas). It uses the
internal class _DataRecords for the actual implementation (it
is kept internal to allow for changes in implementation in the
future, so don't use it directly).

BinaryAppDataStore wasn't designed to be the fastest class out
there, but I'll be surprised if it won't fill all your needs
with zero delay, because binary application files are usually
small and consist of a small amount of records.

==================================================

Copyright (C) 2008, Eli Bendersky (http://eli.thegreenplace.net)
License: This code is in the public domain
"""
from binascii import hexlify, unhexlify
from itertools import islice
from operator import itemgetter
import re, sys
from struct import pack, unpack


class Error(Exception):  pass
class InvalidRecordError(Error): pass
class RecordClashError(Error): pass
class ArgumentError(Error): pass
class InputFileError(Error): pass
class InputRecordError(Error): pass


class BinaryAppDataStore(object):
    """ A store for binary application data.
    """
    def __init__(self):
        self.r = _DataRecords()
        self.start_address = 0

    def record(self, i):
        """ Access the i-th record in the store.
            A (start address, data) tuple is returned.

            Accessing a non-existent record will throw IndexError
        """
        return self.r.record(i)

    def num_records(self):
        """ Number of records in the store
        """
        return self.r.num_records()

    def records(self):
        """ Iterate over the records. Each item is a tuple
            (start address, data).

            Example:

                b = BinaryAppData()
                ... # add some records or file data

                for rec_addr, rec_data in b.records():
                    # rec_addr holds the start address of the
                    # record, and rec_data is the record data
        """
        return self.r.records()

    def iter_addr_data(self):
        """ Iterate over (address, data) pairs of all the contents
            of the store.

            Example:

                for (addr, data) in b.iter_addr_data():
                    print "At %s, data is %s" % (addr, data)
        """
        for rec_addr, rec_data in self.records():
            for offset in range(len(rec_data)):
                yield (rec_addr + offset, rec_data[offset])

    def __iter__(self):
        """ Iterate over the store's data contents.

            Example:

                for data_byte in b:
                    print data_byte

            Note that it returns only the data bytes, without
            their addresses. To iterate over (addr, data) pairs
            use iter_addr_data()
        """
        return iter(map(itemgetter(1), self.iter_addr_data()))

    def __len__(self):
        """ The total amount of data in the store
        """
        return len(self.r)

    def __getitem__(self, addr):
        """ Data item retrieval (by address) from the store.
            Given a store b, b[addr] retrieves the data item at
            'addr'.

            Raises IndexError when the store has no such address
        """
        return self.r[addr]

    def add_record(self, address, data, merge=False):
        """ Directly add a record to the data store.
            The record has a start address and a data string.

            If merge is True, will try to merge the new record
            with its neighbors, if applicable (if the new record
            and one or both of its neighbors form a consecutive
            record).
        """
        self.r.add_record(address, data, merge)


class DataFormatterBinary(object):
    """ Formatter for raw binary data.
    """
    def __init__(self, data=None):
        self.data = data or BinaryAppDataStore()

    def read(self, str=None, filename=None, addr=0):
        """ Read binary data and return a store object. The data
            store is also saved in the interal 'data' attribute.

            The data can either be taken from a string (str
            argument) or a file (provide a filename, which will
            be read in binary mode). If both are provided, the str
            will be used. If neither is provided, an ArgumentError
            is raised.

            Optionally, you can provide a destination address for
            the data. If none is provided, 0 will be used.

            Note: if the store already contains data, this
            operation may result in a RecordClashError.
        """
        if str is None:
            if filename is None:
                raise ArgumentError('Please supply a string or a filename')

            file = open(filename, 'rb')
            str = file.read()
            file.close()

        self.data = BinaryAppDataStore()
        self.data.add_record(addr, str, merge=True)
        return self.data

    def write(self, filename=None, padbyte=None, padtosize=None):
        """ Writes the internal store in binary format.

            If a filename is provided, the data is written to the
            named file. Otherwise, the data is returned as a
            string.

            Padding:

            The records in the data store might be inconsecutive,
            so the output will have to be padded. The padding
            is applied:
              - Before the first record, if it doesn't start at 0
              - Between inconsecutive records
              - After the last record and up until padtosize, if
                that is provided (padtosize is ignored if no
                padbyte is given)

            If padbyte isn't provided, no padding will be done.
            If padbyte is provided, it will be taken as a single
            byte stored in a string (for example 'a' or '\x61').

            Warning: if the records in your data store don't begin
            at 0 or aren't consecutive, beware of padding. A
            single record beginning at 50,000,000 and having two
            bytes will result in a 50-Meg file.
        """
        str = _datastore2string(self.data, padbyte, padtosize)

        if filename:
            file = open(filename, 'wb')
            file.write(str)
            file.close()
        else:
            return str


class DataFormatterHexpair(object):
    """ Formatter for hexpair data.
    """
    def __init__(self, data=None):
        self.data = data or BinaryAppDataStore()

    def read(self, str=None, filename=None, addr=0):
        """ Works similarly to read() in DataFormatterBinary.

            In addition, may throw InputFileError if the input
            file is not formatted correctly.
        """
        if str is None:
            if filename is None:
                raise ArgumentError('Please supply a string or a filename')

            file = open(filename, 'r')
            str = file.read()
            file.close()

        # remove all the separators
        str = re.sub('[^a-fA-F0-9]', '', str)

        try:
            data = unhexlify(str)
        except TypeError:
            err = sys.exc_info()[1]
            raise InputFileError('hexpair string invalid: %s' % err.message)

        self.data = BinaryAppDataStore()
        self.data.add_record(addr, data, merge=True)
        return self.data

    def write(self, filename=None, padbyte=None, padtosize=None,
                linelength=80, separator=' '):
        """ Works similarly to DataFormatterBinary.write(),
            with some of extra parameters.

            linelength:
                The output will be split to lines with maximum
                linelength characters (including the separators,
                but not including newlines).
                If negative, output will be a single line.
                If positive, must be large enough to accomodate
                a single hexpair + separator.

            separator:
                The separator to insert between each hex pair.
        """
        binstr = _datastore2string(self.data, padbyte, padtosize)
        hexpair_str = separator.join(string2hexpairs(binstr)).upper()

        if linelength > 0:
            # length of a single unit: a hexpair (two chars) with
            # a separator
            #
            unit_len = 2 + len(separator)

            if linelength < unit_len:
                raise ArgumentError('linelength too short')

            # adjust the linelength to contain an integral amount
            # of units
            #
            linelength -= linelength % unit_len

            lines = split_subsequences(hexpair_str, linelength)
            hexpair_str = '\n'.join(lines) + '\n'

        if filename:
            file = open(filename, 'w')
            file.write(hexpair_str)
            file.close()
        else:
            return hexpair_str


_64K = 0x10000


class DataFormatterIntelHex(object):
    def __init__(self, data=None):
        self.data = data or BinaryAppDataStore()

    def read(self, str=None, filename=None, addr=0):
        """ Works similarly to read() in DataFormatterBinary.

            An Intel Hex file may specify its load address. In
            such a case, the addr argument is ignored.

            Can raise InputFileError on errors in the input file.
        """
        if str is None:
            if filename is None:
                raise ArgumentError('Please supply a string or a filename')

            str = open(filename, 'r').read()

        # At any stage in the parsing of an Intel Hex file,
        # there's an address offset that have been computed in
        # an earlier line. Such offsets can either be linear or
        # segment. Initially, the offset is in addr, and we
        # assume the offset is linear.
        #
        addr_offset = addr
        is_linear_offset = True

        MAX_64K = 0xffff
        MAX_4G = 0xffffffff

        for linenum, line in enumerate(str.splitlines()):
            def line_error(msg):
                raise InputFileError('error in line %s: %s' % (linenum + 1, msg))

            line = line.strip()
            if not line: continue

            try:
                type, record_offset, data = self._parse_line(line)
            except self._LineError:
                err = sys.exc_info()[1]
                line_error(err.message)

            # The algorithm: each line will be added to the data
            # store as a separate record, relying on record
            # merging to compact the data as much as possible.
            #
            if type == 'Data':
                load_addr = 0

                if is_linear_offset:
                    load_addr = addr_offset + record_offset

                    # (LBA + DRLO + DRI) MOD 4G
                    #
                    # Records that extend beyond the 4G boundary
                    # must be cut in two, and wrapped around to
                    # LBA (addr_offset)
                    #
                    if load_addr + len(data) > MAX_4G + 1:
                        # compute the length of data that will fit
                        # until MAX_4G
                        #
                        fit_len = MAX_4G + 1 - load_addr

                        # Place the data that fits in the end
                        #
                        self.data.add_record(   load_addr,
                                                data[0:fit_len],
                                                merge=True)

                        # And whatever didn't fit at addr_offset
                        #
                        self.data.add_record(   addr_offset,
                                                data[fit_len:],
                                                merge=True)
                    else:
                        # the record fits, so just add it
                        #
                        self.data.add_record(   load_addr, data,
                                                merge=True)
                else:
                    # SBA + ([DRLO + DRI] MOD 64K)
                    # data is wrapped around 64K boundaries
                    #
                    if record_offset + len(data) > MAX_64K + 1:
                        fit_len = MAX_64K + 1 - record_offset
                        self.data.add_record(   addr_offset + record_offset,
                                                data[0:fit_len],
                                                merge=True)
                        self.data.add_record(   addr_offset,
                                                data[fit_len:],
                                                merge=True)
                    else:
                        self.data.add_record(   addr_offset + record_offset, data,
                                                merge=True)

            elif type == 'EndFile':
                return self.data

            elif type in ('LinearOffset', 'SegmentOffset'):
                if len(data) != 2:
                    line_error('expecting a 2-byte data field for this record type, got %s' % len(data))
                field_val = unpack('>H', data)[0]

                if type == 'SegmentOffset':
                    is_linear_offset = False
                    addr_offset = field_val << 4
                else:
                    is_linear_offset = True
                    addr_offset = field_val << 16

            elif type == 'LinearStartAddr':
                if len(data) != 4:
                    line_error('expecting a 4-byte data field for this record type, got %s' % len(data))
                self.data.start_address = unpack('>L', data)[0]

            elif type == 'SegmentStartAddr':
                if len(data) != 4:
                    line_error('expecting a 4-byte data field for this record type, got %s' % len(data))

                (cs, ip) = unpack('>HH', data)
                self.data.start_address = (cs << 4) + ip
            else:
                assert 0, 'Unexpected type %s' % type

        return self.data

    def write(  self,
                filename=None,
                bytes_per_data_line=32,
                write_start_address=False,
                use_segment_addressing=False):
        """ Writes the internal store in Intel HEX format.

            If a filename is provided, the data is written to the
            named file. Otherwise, the data is returned as a
            string.

            Note that files output in Intel HEX require no
            padding, since records will be split to begin at
            different addresses.

            bytes_per_data_line:
                The maximal amount of bytes to output in one line
                of data records. Although the format allows 256,
                it is customary to print out only 32 (probably
                because it's a round (in base 16) number that
                makes the output fit in a 80-char line).

            write_start_address:
                If True, the start address of the data store will
                be written to the output as a separate record
                (type 05 or 03)

            use_segment_addressing:
                If True, the 16-bit segment addressing will be
                used for output. Note that in this case the size
                of the addressable memory is 1 MB.
        """
        if bytes_per_data_line > 256:
            raise ArgumentError('bytes_per_data_line must be <= 256')

        # How this works:
        #
        # First some nomenclature:
        # <<
        # In the jargon of pybinaryappdata, a data store
        # (BinaryAppData) consists of 'records'.
        # Unfortunately, this collides with the jargon of Intel
        # Hex files, where each line is a record of some type. To
        # avoid confusion, I'll refer to Intel HEX records as
        # 'lines'. 'Records' are BinaryAppData records.
        # >>
        #
        # Records are assumed to be non-consecutive (otherwise
        # they would be merged on creation). If they're
        # consecutive, the output will still be correct, though
        # it will contain a few unnecessary lines.
        #
        # For each record, an address offset line is specified,
        # followed by lines listing the record's data. If the
        # record is larger than 64K (the maximal offset allowable
        # in data lines), it is split to several blocks (which
        # follow one another). For example, if the data store
        # consists of a single 100K record at address 0, it is
        # split to two - the first is given an offset 0 and has
        # 64K data items, and the second is given an offset 64K
        # and contains 36K data items.
        #
        # At the end of the file, the start address and
        # end-of-file lines are written.
        #
        output = []

        for rec_start, rec_data in self.data.records():
            rec_end = rec_start + len(rec_data)

            if (use_segment_addressing and rec_end > 0xFFFFF or
                rec_end > 0xFFFFFFFF):
                raise InputRecordError("record at %s-%s won't fit in memory" % (rec_start, rec_end))

            # The following few lines compute the blocks to which
            # this record has to be split. The maximal size of
            # a block is 64K
            #
            blocks_64K = [rec_start]
            i = rec_start + _64K - (rec_start % _64K)

            while i < rec_end:
                blocks_64K.append(i)
                i += _64K

            data_ptr = 0

            #~ print "Rec:", rec_start, rec_end, '> blocks:', blocks_64K

            # Now, for each block, write an address offset
            # line, and compute the amount of data to include in
            # the block.
            # Then, generate the data lines for the block.
            #
            for i, block_start in enumerate(blocks_64K):
                offset_64K = (block_start - block_start % _64K) / _64K

                if use_segment_addressing:
                    assert offset_64K < 16
                    usba = offset_64K << 12
                    output.append(self._make_segment_address_line(usba))
                else:
                    ulba = offset_64K
                    output.append(self._make_linear_address_line(ulba))

                # Block length:
                # All blocks are size _64K, except maybe the first
                # and the last.
                # The first takes up the length needed to complete
                # its offset to the first 64K boundary.
                # The last is computed as follows:
                #  The total data length is taken, and the start
                #  of the block is subtracted. This still doesn't
                #  give the final answer, becase the data began
                #  at an offset, which is reflected in the start
                #  of the first block.
                #
                if i == 0:
                    block_len = _64K - block_start % _64K
                elif i == len(blocks_64K) - 1:
                    block_len = len(rec_data) - block_start + blocks_64K[0]
                else:
                    block_len = _64K

                #~ print '    block:', block_start, block_len, ulba

                output += self._block_data_lines(
                            block_start % _64K,
                            rec_data[data_ptr : data_ptr + block_len],
                            bytes_per_data_line)

                data_ptr += block_len

        if write_start_address:
            if use_segment_addressing:
                output.append(self._make_segment_start_address_line())
            else:
                output.append(self._make_linear_start_address_line())

        output.append(self._make_endfile_line())
        str = '\n'.join(output) + '\n'

        if filename:
            file = open(filename, 'w')
            file.write(str)
            file.close()
        else:
            return str

    def _block_data_lines(self, offset, data, bytes_per_line):
        # Splits a block of data that begins at some offset into
        # Intel HEX record lines, and returns the list of lines.
        #
        lines = []
        data_ptr = 0
        #~ print "bdl:", offset, len(data)

        # Advance bytes_per_line at at time.
        #   offset: the load offset field of the line
        #   data_ptr: pointer into the data from which the next
        #     line will be taken
        #
        while data_ptr < len(data):
            if data_ptr + bytes_per_line > len(data):
                num_bytes_in_line = len(data) - data_ptr
            else:
                num_bytes_in_line = bytes_per_line

            lines.append(self._make_data_line(
                            offset,
                            data[data_ptr:data_ptr + num_bytes_in_line]))

            offset += num_bytes_in_line
            data_ptr += num_bytes_in_line

        return lines

    def _make_checksum(self, line):
        chksum = 0
        for c in line:
            chksum = (chksum + ord(c)) % 256
        return chr((256 - chksum) % 256)

    def _format_line(self, data):
        """ Given the data for a line, computes its checksum,
            prepends ':' and hexlifies all the data bytes to
            produce a valid line of Intel HEX file.
        """
        data_with_checksum = data + self._make_checksum(data)
        return (':' + hexlify(data_with_checksum).upper())

    def _make_linear_address_line(self, ulba):
        line = '\x02\x00\x00\x04' + pack('>H', ulba)
        return self._format_line(line)

    def _make_segment_address_line(self, usba):
        line = '\x02\x00\x00\x02' + pack('>H', usba)
        return self._format_line(line)

    def _make_data_line(self, offset, data):
        line = chr(len(data)) + pack('>H', offset) + '\x00' + data
        return self._format_line(line)

    def _make_segment_start_address_line(self):
        cs = (self.data.start_address / _64K) << 12
        ip = (self.data.start_address % _64K)
        line = '\x04\x00\x00\x03' + pack('>HH', cs, ip)
        return self._format_line(line)

    def _make_linear_start_address_line(self):
        line = '\x04\x00\x00\x05' + pack('>L', self.data.start_address)
        return self._format_line(line)

    def _make_endfile_line(self):
        return ':00000001FF'


    ######################--   PRIVATE   --######################

    class _LineError(Exception): pass

    def _parse_line(self, line):
        """ Parses a line from an Intel Hex file. The line is as
            read from the file.
            Recognizes the line type, makes sure it's formatted
            correctly, and checks the checksum.

            If the line is valid, returns the tuple:
                type, offset, data

                type: a _LineType value
                offset: value of the offset field  (integer)
                data: a binary string with the line's data

            If the line is invalid, throws _LineError with an
            explanatory message.
        """
        # the absolute minimal length of a valid line is 11
        # (1 for ':', 2 for record length, 4 for offset, 2 for
        # type, 0 for data and 2 for checksum)
        #
        if len(line) < 11:
            raise self._LineError('line too short')

        if line[0] != ":":
            raise self._LineError("line does not begin with ':'")

        try:
            length = int(line[1:3], 16)
            offset = int(line[3:7], 16)
            type = int(line[7:9], 16)
            checksum = int(line[-2:], 16)
        except (TypeError, ValueError):
            err = sys.exc_info()[1]
            raise self._LineError(err.message)

        try:
            data = unhexlify(line[9:-2])
        except TypeError:
            err = sys.exc_info()[1]
            raise self._LineError('bad data field: %s' % err.message)

        if len(data) != length:
            raise self._LineError('data field length (%s) not as specified (%s)' % (
                len(data), length))

        # validate checksum
        checksum_test = (length + offset % 256 + offset // 256 + type + checksum) % 256
        for byte in data:
            checksum_test = (checksum_test + ord(byte)) % 256

        if checksum_test != 0:
            expected = (checksum - checksum_test) % 256
            raise self._LineError('checksum test fails: expected %X' % expected)

        rectypes = {
            0: 'Data',
            1: 'EndFile',
            2: 'SegmentOffset',
            3: 'SegmentStartAddr',
            4: 'LinearOffset',
            5: 'LinearStartAddr'}

        if not rectypes.has_key(type):
            raise self._LineError('unknown record type: %s' % line[7:9])

        return rectypes[type], offset, data


def _datastore2string(data, padbyte=None, padtosize=None):
    """ A helper function for packing the whole data store into
        a string.

        See DataFormatterBinary.write() for the explanation of
        parameters.
    """
    str = ''

    if data.num_records() == 0:
        return str

    # If the first record doesn't begin at 0, maybe we should
    # pad the data from 0
    #
    first_record_start = data.record(0)[0]
    if first_record_start != 0 and padbyte:
        str += padbyte * first_record_start

    # Add all the records to the string. First pad them, if
    # necessary.
    #
    # prev_record_end is initialized to first_record_start - 1
    # to cleanly handle the first record without extra checks.
    #
    prev_record_end = first_record_start - 1
    for rec_start, rec_data in data.records():
        if prev_record_end + 1 != rec_start and padbyte:
            str += padbyte * (rec_start - prev_record_end - 1)

        str += rec_data
        prev_record_end = rec_start + len(rec_data) - 1

    # Pad until padtosize if requested
    #
    if padbyte and padtosize and padtosize > prev_record_end + 1:
        str += padbyte * (padtosize - prev_record_end - 1)

    return str


class _DataRecords(object):
    """ Implements a collection of 'records'. Each record holds
        a consecutive segment of data.

        Serves as the low-level implementation of the high-level
        interface exposed in BinaryAppDataStore.
    """
    def clear(self):
        self.d = []
        self.len = 0

    def __init__(self):
        self.clear()

    def __len__(self):
        return self.len

    def __getitem__(self, addr):
        """ Access to the byte at address 'addr'
        """
        (recnum, offset) = self._find_address(addr)
        return self.d[recnum].data[offset]

    def record(self, i):
        """ The i-th record (start, data) tuple
        """
        r = self.d[i]
        return (r.start, r.data)

    def num_records(self):
        """ Number of records
        """
        return len(self.d)

    def records(self):
        """ An iterator of records
        """
        for r in self.d:
            yield (r.start, r.data)

    def add_record(self, address, data, merge=False):
        def find_index(lo, hi):
            """ Finds the position to insert the record in, using
                binary search.
                Doesn't check record clashes.
            """
            i = (hi + lo) // 2
            #~ print 'fi:', i

            if self.d[i].start > address:
                return 0 if i == 0 else find_index(lo, i)
            elif i == len(self.d) - 1:
                return i + 1
            elif self.d[i + 1].start > address:
                return i + 1
            else:
                return find_index(i, hi)

        def segments_intersect(s1, e1, s2, e2):
            """ Do the segments [s1:e1] and [s2:e2] intersect ?
                Note: the segment ranges are inclusive, and all
                end-points are natural. Also, eN >= sN always.
            """
            return e1 >= s2 and e2 >= s1

        # If we're empty, no need to search
        #
        if len(self.d) == 0:
            self.d = [self._make_record_addr_data(address, data)]
        # Otherwise find the index to insert the record in
        #
        else:
            i = find_index(0, len(self.d))

            rec_start = address
            rec_end = address + len(data) - 1

            # Check that the new record doesn't clash with its
            # neighbors
            #
            if i > 0 and segments_intersect(
                            rec_start, rec_end,
                            self.d[i - 1].start, self.d[i - 1].end):
                msg = "Added record clashes with existing record at %s:%s" % (
                    self.d[i - 1].start, self.d[i - 1].end)
                raise RecordClashError(msg)
            if i < len(self.d) and segments_intersect(
                            rec_start, rec_end,
                            self.d[i].start, self.d[i].end):
                msg = "Added record clashes with existing record at %s:%s" % (
                    self.d[i].start, self.d[i].end)
                raise RecordClashError(msg)

            merged_left = False
            merged_right = False

            # If merging is requested, attempt to merge with
            # neighbor records
            #
            if merge:
                # to the left...
                if i > 0 and self.d[i - 1].end == rec_start - 1:
                    self.d[i - 1].end = rec_end
                    self.d[i - 1].data += data
                    merged_left = True
                # to the right
                elif (  i < len(self.d) and
                        rec_end == self.d[i].start - 1):
                    self.d[i].start = rec_start
                    self.d[i].data = data + self.d[i].data
                    merged_right = True

                # and now, maybe we can merge'em all !
                if (    0 < i < len(self.d) and
                        self.d[i - 1].end == self.d[i].start - 1):
                    self.d[i - 1].end = self.d[i].end
                    self.d[i - 1].data += self.d[i].data
                    del self.d[i]

            if not merge or not (merged_left or merged_right):
                # Insert the new record into its place
                #
                self.d.insert(i,
                    self._Record(rec_start, rec_end, data))

        self.len += len(data)

    ######################--   PRIVATE   --######################

    # Holds a consecutive 'record' of data. It has a start
    # address, an end address and the data string.
    # len(data) == end - start + 1
    #
    class _Record(object):
        def __init__(self, start, end, data):
            if end < start or len(data) != end - start + 1:
                msg = 'data len: %s, start: %s, end: %s' % (
                    len(data), start, end)
                raise InvalidRecordError(msg)

            self.start = start
            self.end = end
            self.data = data

        def __repr__(self):
            return "[%s:%s] '%s'" % (self.start, self.end, self.data)

    def _make_record_addr_data(self, address, data):
        return self._Record(address, address + len(data) - 1, data)

    def _find_address(self, addr):
        """ Finds a data cell with the given address. Returns
            a pair (recnum, offset):
                recnum: record number
                offset: offset to the requested address
            The data can then be accessed as
            self.d[recnum].data[offset]

            If such an address doesn't exist in any record,
            returns None.
        """

        # binary search between lo and hi, inclusive
        def search(lo, hi):
            if lo > hi:
                raise IndexError('No address %s in records' % addr)

            i = (hi + lo) // 2

            if self.d[i].start > addr:
                return search(lo, i - 1)
            else:
                if self.d[i].end >= addr:
                    return (i, addr - self.d[i].start)
                else:
                    return search(i + 1, hi)

        return search(0, len(self.d) - 1)


def split_subsequences(iterable, length=2, overlap=0,
                        join_substr=True):
    """ Given an iterable, splits it to subsequences of the given
        length (possibly with overlapping), and returns an
        iterator of the subsequences.

        If join_substr is set to True and iterable is a string,
        the subsqeuences will be joined (with '') into substrings.
    """
    isstring = isinstance(iterable, str) and join_substr
    it = iter(iterable)
    results = list(itertools.islice(it, length))
    while len(results) == length:
        yield ''.join(results) if isstring else results
        results = results[length - overlap:]
        results.extend(itertools.islice(it, length - overlap))
    if results:
        yield ''.join(results) if isstring else results


def string2hexpairs(str):
    """ Given a string denoting binary data, splits it to a list
        of 'hexpairs', such as ['A8', 'FF']
    """
    return list(split_subsequences(binascii.hexlify(str), 2))
