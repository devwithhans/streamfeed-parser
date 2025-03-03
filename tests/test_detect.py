import pytest
from streamfeed.detect import detect_compression_from_bytes, detect_separator


def test_detect_compression_from_bytes():
    assert detect_compression_from_bytes(b"PK") == "zip"
    assert detect_compression_from_bytes(b"\x1f\x8b") == "gz"
    assert detect_compression_from_bytes(b"BZh") == "bz2"
    assert detect_compression_from_bytes(b"\x75\x73\x74\x61\x72") == "tar"
    assert detect_compression_from_bytes(b"random") is None


def test_detect_separator():
    sample = "name,age\nJohn,30\nAlice,25"
    delimiter, quotechar = detect_separator(sample)
    assert delimiter == ","
    assert quotechar == '"'
