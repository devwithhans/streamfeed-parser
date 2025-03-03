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
from .ftp_handler import stream_from_ftp
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

    # Example override for some custom URL checks
    if "datafeedwatch" in url:
        item_tag = "item"

    try:
        if is_ftp:
            # For FTP URLs, we download the content and create a file-like object
            content = stream_from_ftp(url)
            file_obj = io.BytesIO(content)

            if compression_type == "zip":
                with zipfile.ZipFile(file_obj, "r") as z:
                    for name in z.namelist():
                        with z.open(name, "r") as f:
                            if is_xml:
                                yield from stream_xml_items_iterparse(
                                    f, item_tag=item_tag, limit_rows=limit_rows
                                )
                            else:
                                lines_gen = (
                                    line.decode("utf-8", errors="replace") for line in f
                                )
                                yield from stream_csv_lines(
                                    lines_gen, limit_rows, max_field_length
                                )

            elif compression_type == "gz":
                with gzip.GzipFile(fileobj=file_obj) as gz:
                    if is_xml:
                        yield from stream_xml_items_iterparse(
                            gz, item_tag=item_tag, limit_rows=limit_rows
                        )
                    else:
                        lines_gen = (
                            line.decode("utf-8", errors="replace") for line in gz
                        )
                        yield from stream_csv_lines(
                            lines_gen, limit_rows, max_field_length
                        )

            elif compression_type == "bz2":
                with bz2.BZ2File(file_obj) as bz:
                    if is_xml:
                        yield from stream_xml_items_iterparse(
                            bz, item_tag=item_tag, limit_rows=limit_rows
                        )
                    else:
                        lines_gen = (
                            line.decode("utf-8", errors="replace") for line in bz
                        )
                        yield from stream_csv_lines(
                            lines_gen, limit_rows, max_field_length
                        )

            else:  # No compression or unsupported
                if is_xml:
                    yield from stream_xml_items_iterparse(
                        file_obj, item_tag=item_tag, limit_rows=limit_rows
                    )
                else:
                    lines_gen = (
                        line.decode("utf-8", errors="replace") for line in file_obj
                    )
                    yield from stream_csv_lines(lines_gen, limit_rows, max_field_length)

        else:  # HTTP/HTTPS URLs
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

            # Apply explode logic on top of the raw rows
            yield from explode_rows(raw_rows, feed_logic)

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
