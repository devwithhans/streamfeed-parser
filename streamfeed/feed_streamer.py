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
from .ftp_handler import FTPResponse
from .xml_parser import stream_xml_items_iterparse, stream_xml_feed
from .csv_parser import stream_csv_lines, stream_csv_feed
from .transform import explode_rows


def stream_feed(
    url: str,
    feed_logic: Optional[Dict[str, Any]] = None,
    limit_rows: Optional[int] = None,
    max_field_length: Optional[int] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Stream feed rows from a URL, detecting compression and whether
    it's CSV vs. XML. For XML, use the input variable item_tag from feed_logic (default 'product').
    Now supports both HTTP(S) and FTP protocols in a streaming manner.
    """
    # Check if this is an FTP URL
    is_ftp = url.lower().startswith("ftp://")

    # Detect compression and check for XML
    compression_type = detect_compression_from_url_or_content(url)
    file_lower = url.lower()
    is_xml = "xml" in file_lower

    # Determine the XML item tag from feed_logic, defaulting to 'product'
    item_tag = feed_logic.get("xml_item_tag", "product") if feed_logic else "product"

    # Example override for some custom URL checks
    if "datafeedwatch" in url:
        item_tag = "item"

    try:
        if is_ftp:
            # Use our FTPResponse class for streaming
            response = FTPResponse(url)
            # There's no explicit "status" to raise, so no raise_for_status()
        else:
            # Normal HTTP(S) path
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

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

        # Apply "explode" logic on top of the raw rows
        yield from explode_rows(raw_rows, feed_logic)

    except Exception as e:
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
