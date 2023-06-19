import os
import struct
import pandas as pd
import io

import pytest
from conftest import odc_modules

from pyodc import codec
from pyodc.constants import DataType
from pyodc.stream import LittleEndianStream


def _check_decode(cdc, encoded, check):
    st = LittleEndianStream(encoded)
    v = cdc.decode(st)
    assert v == check


def test_null_terminated_constant_string():
    """
    This tests the (somewhat dubious) 'missing' values in some (older) data
    encoded from ODB-1 using the migrator. This data uses the integer missing value,
    casted to a double, that happens to start with \x00 --> "NULL STRING"

    We need to support decoding this data...
    """
    constant_value = struct.unpack("<d", b"\x00\x00\xc0\xff\xff\xff\xdfA")[0]
    cdc = codec.ConstantString("column", constant_value, constant_value, DataType.STRING, has_missing=False)
    encoded = b""

    _check_decode(cdc, encoded, "")


def test_stripped_constant_string():
    constant_value = struct.unpack("<d", b"hello\x00\x00\x00")[0]
    cdc = codec.ConstantString("column", constant_value, constant_value, DataType.STRING, has_missing=False)
    encoded = b""

    _check_decode(cdc, encoded, "hello")


def test_normal_constant_string():
    constant_value = struct.unpack("<d", b"helloAAA")[0]
    cdc = codec.ConstantString("column", constant_value, constant_value, DataType.STRING, has_missing=False)
    encoded = b""

    _check_decode(cdc, encoded, "helloAAA")

def test_string_codec_selection():
    # Deliberately using strings on length 7,8,9 to catch edges cases
    testcases = [
        [["constan", "constan"], codec.ConstantString],
        [["constant", "constant"], codec.ConstantString],
        [["longconst", "longconst"], codec.VariableLengthConstantString],
        [["longconstant", "longconstant"], codec.VariableLengthConstantString],
        [["not", "constant", "longnotconstant"], codec.Int8String],
        [["longconstant"] + [str(num) for num in range(256)], codec.Int16String]
    ]


    for testdata, expected_codec in testcases:
        # Check that the correct codec is being selected
        series = pd.Series(testdata)
        selected_codec = codec.select_codec("column", series, DataType.STRING, False)
        assert isinstance(selected_codec, expected_codec)
        
        # Create a temporary stream
        f = io.BytesIO()
        st = LittleEndianStream(f)
        
        # Encode the header and data for just this column        
        selected_codec.encode_header(st)
        for val in testdata: selected_codec.encode(st, val)
        st.seek(0) # reset the stream to the start
        
        # Check the header can be decoded correctly
        decoded_codec = codec.read_codec(st)
        assert decoded_codec.column_name == "column"
        assert decoded_codec.type == DataType.STRING
        assert decoded_codec.name == selected_codec.name
        
        # Check the encoded data matches        
        for val in testdata:
            decoded_val = selected_codec.decode(st)
            assert val == decoded_val


@pytest.mark.parametrize("odyssey", odc_modules)
def test_decode_odb1_missing_strings(odyssey):
    """
    Tests that we can decode missing (NULL) strings from data encoded
    from ODB-1 using the migrator. This data uses the integer missing value,
    casted to a double, that happens to start with \x00.

    The test sample contains valid data pre-encoded (which cannot be encoded
    through the python API, as we (correctly) encode the missing value as a
    null string).
    """
    with open(os.path.join(os.path.dirname(__file__), "data/odb1_missing_string.odb"), "rb") as f:
        df = odyssey.read_odb(f, single=True)

    assert df.shape == (4, 1)
    series = df["col1"]
    assert series.dtype == "object"

    for v in series:
        assert isinstance(v, str)
        assert v == ""
