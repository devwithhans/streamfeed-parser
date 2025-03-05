import pytest
from unittest.mock import patch, MagicMock
from streamfeed.ftp_handler import parse_ftp_url, stream_ftp_file


def test_parse_ftp_url():
    url = "ftp://user:pass@example.com/path/to/file.csv"
    host, username, password, path = parse_ftp_url(url)
    assert host == "example.com"
    assert username == "user"
    assert password == "pass"
    assert path == "/path/to/file.csv"


@patch("ftplib.FTP")
def test_stream_from_ftp(mock_ftp):
    mock_ftp_instance = MagicMock()
    mock_ftp.return_value = mock_ftp_instance

    mock_ftp_instance.retrbinary.side_effect = lambda cmd, callback: callback(
        b"sample data"
    )

    url = "ftp://example.com/path/to/file.csv"
    result = stream_from_ftp(url)

    assert result == b"sample data"
