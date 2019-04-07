import os
import struct
from .errors import Error

try:
    from .cbsdiff import pack_size
except ImportError:
    from .bsdiff import pack_size


PATCH_TYPE_NORMAL    = 0
PATCH_TYPE_IN_PLACE  = 1

COMPRESSIONS = {
    'none': 0,
    'lzma': 1,
    'crle': 2
}

DATA_FORMAT_ARM_CORTEX_M4 = 0
DATA_FORMAT_AARCH64       = 1

DATA_FORMATS = {
    'arm-cortex-m4': DATA_FORMAT_ARM_CORTEX_M4,
    'aarch64': DATA_FORMAT_AARCH64
}


def format_or(items):
    items = [str(item) for item in items]

    if len(items) == 1:
        return items[0]
    else:
        return '{} or {}'.format(', '.join(items[:-1]),
                                 items[-1])


def format_bad_compression_string(compression):
    return "Expected compression {}, but got {}.".format(
        format_or(sorted(COMPRESSIONS)),
        compression)


def format_bad_compression_number(compression):
    items = sorted([(n, '{}({})'.format(s, n)) for s, n in COMPRESSIONS.items()])

    return "Expected compression {}, but got {}.".format(
        format_or([v for _, v in items]),
        compression)


def format_bad_data_format(data_format):
    return 'Expected data format {}, but got {}.'.format(
        format_or(sorted(DATA_FORMATS)),
        data_format)


def format_bad_data_format_number(data_format):
    items = sorted([(n, '{}({})'.format(s, n)) for s, n in DATA_FORMATS.items()])

    return "Expected data format {}, but got {}.".format(
        format_or([v for _, v in items]),
        data_format)


def compression_string_to_number(compression):
    try:
        return COMPRESSIONS[compression]
    except KeyError:
        raise Error(format_bad_compression_string(compression))


def data_format_number_to_string(data_format):
    for string, number in DATA_FORMATS.items():
        if data_format == number:
            return string

    raise Error(format_bad_data_format_number(data_format))


def div_ceil(a, b):
    return (a + b - 1) // b


def file_size(f):
    position = f.tell()
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(position, os.SEEK_SET)

    return size


def file_read(f):
    f.seek(0, os.SEEK_SET)

    return f.read()


def unpack_size_with_length(fin):
    try:
        byte = fin.read(1)[0]
    except IndexError:
        raise Error('Failed to read first size byte.')

    is_signed = (byte & 0x40)
    value = (byte & 0x3f)
    offset = 6

    while byte & 0x80:
        try:
            byte = fin.read(1)[0]
        except IndexError:
            raise Error('Failed to read consecutive size byte.')

        value |= ((byte & 0x7f) << offset)
        offset += 7

    if is_signed:
        value *= -1

    return value, ((offset - 6) / 7 + 1)


def unpack_size(fin):
    return unpack_size_with_length(fin)[0]


def pack_usize(value):
    return pack_size(struct.unpack('>q', struct.pack('>Q', value))[0])


def unpack_usize(fin):
    return struct.unpack('>Q', struct.pack('>q', unpack_size(fin)))[0]


class DataSegment(object):

    def __init__(self,
                 from_data_offset,
                 from_data_begin,
                 from_data_end,
                 from_code_begin,
                 from_code_end,
                 to_data_offset,
                 to_data_begin,
                 to_data_end,
                 to_code_begin,
                 to_code_end):
        self.from_data_offset = from_data_offset
        self.from_data_begin = from_data_begin
        self.from_data_end = from_data_end
        self.from_code_begin = from_code_begin
        self.from_code_end = from_code_end
        self.to_data_offset = to_data_offset
        self.to_data_begin = to_data_begin
        self.to_data_end = to_data_end
        self.to_code_begin = to_code_begin
        self.to_code_end = to_code_end
