import requests
import csv
import asyncio
import io
import re
import zipfile
import gzip
import bz2

from typing import Optional, Dict, Any, Iterator, List
from itertools import product


from .detect import detect_compression_from_url_or_content
from .ftp_handler import FTPResponse, get_ftp_size, stream_from_ftp
from .xml_parser import stream_xml_items_iterparse, stream_xml_feed
from .csv_parser import stream_csv_lines, stream_csv_feed
from .transform import explode_rows


class CountingIO:
    def __init__(self, raw_stream):
        self.raw_stream = raw_stream
        self.bytes_read = 0

    def read(self, *args, **kwargs):
        data = self.raw_stream.read(*args, **kwargs)
        self.bytes_read += len(data)
        return data

    def __getattr__(self, name):
        return getattr(self.raw_stream, name)


class StreamResponse:

    def __init__(
        self, content_length: int, data: Dict[str, Any], bytes_read: Optional[int] = 0
    ):

        self.content_length: int = content_length
        self.bytes_read: int = bytes_read
        self.data: Dict[str, Any] = data

    def dict(self):
        return {
            "content_lenght": self.content_length,
            "data": self.data,
            "bytes_read": self.bytes_read,
        }


def stream_feed(
    url: str,
    feed_logic: Optional[Dict[str, Any]] = None,
    limit_rows: Optional[int] = None,
    max_field_length: Optional[int] = None,
    add_content_length: Optional[bool] = False,
) -> Iterator[StreamResponse]:
    """
    Stream feed rows from a URL, detecting compression and whether
    it's CSV vs. XML. For XML, use the input variable item_tag from feed_logic (default 'product').
    Supports both HTTP(S) and FTP protocols.
    """
    # Determine if this is an FTP URL
    is_ftp = url.lower().startswith("ftp://")

    # Get compression type and determine if it's XML
    compression_type = detect_compression_from_url_or_content(url)
    file_lower = url.lower()
    is_xml = "xml" in file_lower

    # Determine the XML item tag from feed_logic, defaulting to 'product'
    item_tag = feed_logic.get("xml_item_tag", "product") if feed_logic else "product"
    content_length = None

    def _response(data):
        if add_content_length:
            for row in data:
                # Read bytes from the wrapped .raw
                yield StreamResponse(
                    content_length=content_length,
                    bytes_read=getattr(response.raw, "bytes_read", None),
                    data=row,
                )
        else:
            yield from data

    try:
        print(compression_type)
        print(is_xml)
        if is_ftp:
            ftp_generator = stream_from_ftp(url)
            response = FTPResponse(ftp_generator)
            content_length = get_ftp_size(url)

        else:  # HTTP/HTTPS URLs
            response = requests.get(url, stream=True, timeout=10)
            content_length = int(response.headers.get("Content-Length", 0) or 0)
            response.raise_for_status()

        response.raw = CountingIO(response.raw)

        if is_xml:
            raw_rows = stream_xml_feed(
                response,
                item_tag=item_tag,
                limit_rows=limit_rows,
                decompress_type=compression_type,
            )

        else:
            raw_rows = stream_csv_feed(
                response,
                limit_rows=limit_rows,
                max_field_length=max_field_length,
                decompress_type=compression_type,
            )

        yield from _response(explode_rows(raw_rows, feed_logic))

    except (requests.RequestException, Exception) as e:
        print(f"Error fetching URL: {e}")
        return


def preview_feed(
    url: str,
    feed_logic: Optional[Dict[str, Any]] = None,
    limit_rows: int = 100,
    max_field_length: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Return a preview list of feed rows by reading up to limit_rows rows from the feed.
    """

    return list(
        stream_feed(
            url,
            feed_logic=feed_logic,
            limit_rows=limit_rows,
            max_field_length=max_field_length,
        )
    )
