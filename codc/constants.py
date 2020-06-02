
from .lib import lib
from enum import IntEnum, unique


@unique
class DataType(IntEnum):
    IGNORE = lib.ODC_IGNORE
    INTEGER = lib.ODC_INTEGER
    DOUBLE = lib.ODC_DOUBLE
    REAL = lib.ODC_REAL
    STRING = lib.ODC_STRING
    BITFIELD = lib.ODC_BITFIELD


IGNORE = DataType.IGNORE
INTEGER = DataType.INTEGER
REAL = DataType.REAL
STRING = DataType.STRING
BITFIELD = DataType.BITFIELD
DOUBLE = DataType.DOUBLE

