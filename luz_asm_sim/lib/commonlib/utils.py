# Common utilities  for Luz-related Python code
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2008-2010
#
import struct
import types


MASK_WORD = 0xFFFFFFFF
MASK_HALFWORD = 0xFFFF
MASK_BYTE = 0xFF


def extract_bitfield(num, left, right, reverse=False):
    """ Extract the bit field [left:right] (inclusive)
        from the number. If reverse=True, the bit-field is
        reversed.
        
        Assumes 31 >= left >= right >= 0
        
        Return the integer coded by the bit-field.
        
        Examples:
            extract_bitfield(53, 5, 1) => 26
            extract_bitfield(53, 5, 1, reverse=True) => 11
    """
    field_width = left - right + 1
    field = (num >> right) & (2**field_width- 1)
    
    return reverse_bits(field, field_width) if reverse else field


def build_bitfield(left, right, num):
    """ Builds a bit-field in the specified range [left:right]
        with the value 'num', inside a 32-bit integer, and
        returns it.
        
        For example:
            field(4, 2, 3) 
                => 12
        
        Assumptions:
        *   31 >= left >= right >= 0
        *   The number is assumed to be small enough to fit
            the field. If it isn't, its lowest left-right+1 
            bits are taken.
            
        Note that if you take the low bits as the field (N-1:0) 
        and the number is signed, the result will be correct as
        long as the signed number fits in N bits.
    """
    mask = 2 ** (left - right + 1) - 1
    return (int(num) & mask) << right


def unpack_bytes(str):
    """ A sequence of bytes can be stored in several ways.
        Two of the most common are:
        
        -   A sequence of integer byte values, such as
            (97, 98, 99, 1, 255)
        -   A packed string. For the sequence above it is:
            'abc\x01\xff'
    
        unpack_bytes returns the byte sequence represetation of
        a packed string. It works for strings of arbitrary length.
    
        For example:
        
            >>> unpack_bytes('abc\x01\xff')
            (97, 98, 99, 1, 255)
    """
    return struct.unpack("%sB" % len(str), str)


def pack_bytes(bytes):
    """ Packs a sequence of bytes into a string.
        
        See the doc-string for unpack_bytes for more info.
    """
    return struct.pack("%sB" % len(bytes), *bytes)


_nbytes_format_map = {1: 'b', 2: 'h', 4: 'l'}

def pack_number(num, nbytes=4, big_endian=False, signed=False):
    """ Packs a number into a binary data string representing
        a word of 'nbytes'
    """
    endian = '>' if big_endian else '<'
    specifier = _nbytes_format_map[nbytes]
    if not signed:
        specifier = specifier.upper()
    return struct.pack('%s%s' % (endian, specifier), num)


def unpack_number(str, nbytes=4, big_endian=False, signed=False):
    """ Unpacks a number from a binary data string representing
        a word of 'nbytes'
    """
    endian = '>' if big_endian else '<'
    specifier = _nbytes_format_map[nbytes]
    if not signed:
        specifier = specifier.upper()
    return struct.unpack('%s%s' % (endian, specifier), str)[0]


def pack_word(word, big_endian=False, signed=False):
    """ Packs a 32-bit word into a binary data string.
    """
    return pack_number(word, 4, big_endian, signed)
    

def unpack_word(str, big_endian=False, signed=False):
    """ Unpacks a 32-bit word from a binary data string.
    """
    return unpack_number(str, 4, big_endian, signed)


def pack_halfword(hword, big_endian=False, signed=False):
    """ Packs a 16-bit halfword into a binary data string.
    """
    return pack_number(hword, 2, big_endian, signed)


def unpack_halfword(str, big_endian=False, signed=False):
    """ Unpacks a 16-bit halfword from a binary data string.
    """
    return unpack_number(str, 2, big_endian, signed)


def word2bytes(word, big_endian=False):
    """ Converts a 32-bit word into a list of 4 byte values.
    """
    return unpack_bytes(pack_word(word, big_endian))


def bytes2word(bytes, big_endian=False):
    """ Converts a list of 4 byte values into a 32-bit word.
    """
    return unpack_word(pack_bytes(bytes), big_endian)


def halfword2bytes(hword, big_endian=False):
    """ Converts a 16-bit halfword into a list of 2 byte values.
    """
    return unpack_bytes(pack_halfword(hword, big_endian))


def bytes2halfword(bytes, big_endian=False):
    """ Converts a list of 2 byte values into a 16-bit halfword.
    """
    return unpack_halfword(pack_bytes(bytes), big_endian)


def num_fits_in_nbits(num, nbits, signed=False):
    """ Check if an integer fits into N bits
    """
    if signed:
        return not (num > 2 ** (nbits - 1) - 1 or 
                    num < -(2 ** (nbits - 1)))
    else:
        return not (num > 2 ** nbits - 1 or num < 0)


#
# Signed values are kept in LUZ registers as 32-bit words in 2s 
# complement representation. E.g. -2 is 0xFFFFFFFE
#

def signed_is_negative(num, nbits=32):
    """ Assuming the number is a word in 2s complement, is it 
        negative?
    """
    return num & (1 << (nbits - 1))


def signed2int(num, nbits=32):
    """ Assuming the number is a word in 2s complement,
        return its Python integer value (which can either be 
        positive or negative).
    """
    if signed_is_negative(num, nbits):
        return num - 2 ** nbits
    else:
        return num


def int2signed(num, nbits=32):
    """ Given a Python integer, return its 2s complement 
        word representation.
    """
    if num < 0:
        return 2 ** nbits + num
    else:
        return num
    

def Enum(*names):
    """ Create an enumeration type.
    
        >>> Days = Enum('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
       
        Then use: Days.Mo, Days.Sa, etc.
    """
    assert names, "Empty enums are not supported" # <- Don't like empty enums? Uncomment!

    class EnumClass(object):
        __slots__ = names
        def __iter__(self):         return iter(constants)
        def __len__(self):          return len(constants)
        def __getitem__(self, i):   return constants[i]
        def __repr__(self):         return 'Enum' + str(names)
        def __str__(self):          return 'enum ' + str(constants)

    class EnumValue(object):
        __slots__ = ('__value')
        def __init__(self, value): self.__value = value
            
        Value = property(lambda self: self.__value)
        EnumType = property(lambda self: EnumType)
        
        def __hash__(self):         return hash(self.__value)
        def __invert__(self):       return constants[maximum - self.__value]
        def __nonzero__(self):      return bool(self.__value)
        def __repr__(self):         return str(names[self.__value])

        def __cmp__(self, other):
            if self.EnumType is not other.EnumType:
                return cmp(self.EnumType, other.EnumType)
            else:
                return cmp(self.__value, other.__value)
            
    maximum = len(names) - 1
    constants = [None] * len(names)
    
    for i, each in enumerate(names):
        val = EnumValue(i)
        setattr(EnumClass, each, val)
        constants[i] = val
        
    constants = tuple(constants)
    EnumType = EnumClass()
    return EnumType


#-----------------------------------------------------------------
