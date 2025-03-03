from typing import Optional, Dict, Any, Iterator, List, Union, Tuple
import requests
import csv


def detect_compression_from_bytes(header_bytes: bytes) -> Optional[str]:
    """
    Determine compression type from the first few bytes of the file.
    Return 'zip', 'gz', 'bz2', 'tar', or None if no known compression is detected.
    """
    if header_bytes.startswith(b"PK"):
        return "zip"
    elif header_bytes.startswith(b"\x1f\x8b"):
        return "gz"
    elif header_bytes.startswith(b"BZh"):
        return "bz2"
    elif header_bytes.startswith(b"\x75\x73\x74\x61\x72"):  # "ustar"
        return "tar"
    return None


def detect_compression(url: str, peek_size: int = 1024) -> Optional[str]:
    """
    Perform a streaming GET to read the first few bytes and determine compression type.
    """
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        first_chunk = next(response.iter_content(chunk_size=peek_size), b"")
        if not first_chunk:
            response.close()
            return None
        ctype = detect_compression_from_bytes(first_chunk)
        response.close()
        return ctype
    except Exception as e:
        print(f"Error detecting compression: {e}")
        return None


def detect_separator(sample_text: str) -> Tuple[str, str]:
    """
    Attempt to detect CSV delimiter/quotechar from a sample.
    Fallback to tab-delimited if detection fails.
    """
    sample = sample_text[:4096]  # Use a larger sample for better detection
    try:
        dialect = csv.Sniffer().sniff(sample)
        return (dialect.delimiter, dialect.quotechar)
    except csv.Error:
        # Try some common delimiters
        for delimiter, quotechar in [(",", '"'), ("\t", '"'), (";", '"'), ("|", '"')]:
            try:
                # Test if we can parse at least 3 lines with consistent field counts
                reader = csv.reader(
                    sample.splitlines(), delimiter=delimiter, quotechar=quotechar
                )
                rows = list(reader)[:5]
                if len(rows) >= 2:
                    field_counts = [len(row) for row in rows]
                    # Check if most rows have the same field count
                    if field_counts.count(field_counts[0]) >= len(field_counts) // 2:
                        return (delimiter, quotechar)
            except:
                continue

        # fallback
        return ("\t", '"')


def detect_compression_from_url_or_content(url: str) -> Optional[str]:
    """
    Determine compression type from URL extension or by peeking at content.
    """
    # Check URL extension first
    url_lower = url.lower()
    if url_lower.endswith(".zip"):
        return "zip"
    elif url_lower.endswith(".gz") or url_lower.endswith(".gzip"):
        return "gz"
    elif url_lower.endswith(".bz2"):
        return "bz2"
    elif url_lower.endswith(".tar"):
        return "tar"

    if url.startswith("ftp://"):
        return None
    else:
        # For HTTP(S) URLs, use the existing detection function
        return detect_compression(url)
