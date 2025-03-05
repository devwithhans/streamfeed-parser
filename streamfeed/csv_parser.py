from typing import Optional, Dict, Any, Iterator, List, Union, Tuple
import requests
import zipfile
from .detect import detect_separator
import io
import csv
from itertools import chain, product
import gzip
import bz2


def join_broken_csv_lines(lines_gen: Iterator[str]) -> Iterator[str]:
    """
    Process an iterator of lines and join those that are part of the same CSV record
    due to newlines inside quoted fields.
    """
    buffer = ""
    quote_count = 0
    in_quote = False

    for line in lines_gen:
        if not buffer:
            buffer = line
            # Count quotes in the first line
            quote_count = buffer.count('"')
            in_quote = (
                quote_count % 2 == 1
            )  # Odd number of quotes means we're inside a quoted field
            if not in_quote:
                yield buffer
                buffer = ""
            continue

        # We have content in the buffer, meaning we're inside a quoted field
        buffer += "\n" + line
        quote_count += line.count('"')
        in_quote = quote_count % 2 == 1

        if not in_quote:  # If we're not in a quote anymore, yield the complete record
            yield buffer
            buffer = ""

    # Don't forget any remaining content
    if buffer:
        yield buffer


def stream_csv_lines(
    lines_gen: Iterator[str],
    limit_rows: Optional[int],
    max_field_length: Optional[int],
) -> Iterator[Dict[str, Any]]:
    """
    Given an iterator of lines, parse them as CSV and yield dict rows.
    Handles newlines within quoted fields while maintaining streaming behavior.
    """
    # Sample a few lines for format detection without loading the entire file
    sample_lines = []
    for i, line in enumerate(lines_gen):
        if line.strip():  # Skip empty lines
            sample_lines.append(line)
            if i >= 15:  # Collect a limited sample
                break

    if not sample_lines:
        return  # Empty feed

    # Detect CSV format from the sample
    sample_text = "\n".join(sample_lines)
    delimiter, quotechar = detect_separator(sample_text)

    # Create a streaming CSV processor
    try:
        # Process the header line first
        header = sample_lines[0].strip() if sample_lines else ""
        if not header:
            return

        # Create field names from the header
        fieldnames = None
        if delimiter in header:
            # Use csv.reader to properly parse the header with respect to quotes
            reader = csv.reader([header], delimiter=delimiter, quotechar=quotechar)
            for row in reader:
                fieldnames = [f.strip() for f in row if f.strip()]
                break

        # Fallback if we couldn't parse proper field names
        if not fieldnames:
            # Try comma as universal separator for challenging feeds
            if "," in header:
                fieldnames = [f.strip() for f in header.split(",") if f.strip()]
            else:
                # Create synthetic field names as last resort
                fieldnames = [
                    f"field_{i}"
                    for i in range(
                        len(header.split(delimiter)) if delimiter in header else 10
                    )
                ]

        # Process the remaining sample lines and continue with the generator
        remaining_lines = sample_lines[1:] if len(sample_lines) > 1 else []

        # Create a stream processor for the joined lines
        line_stream = chain(remaining_lines, lines_gen)
        joined_line_stream = join_broken_csv_lines(line_stream)

        count = 0
        buffer = ""
        for line in joined_line_stream:
            if not line.strip():
                continue

            try:
                # Parse each line using csv.reader to handle proper CSV parsing
                csv_reader = csv.reader(
                    [line], delimiter=delimiter, quotechar=quotechar
                )
                row_data = next(csv_reader, None)

                if row_data:
                    # Create the dictionary from fieldnames and row data
                    result = {}
                    for i, value in enumerate(row_data):
                        if i < len(fieldnames):
                            field = fieldnames[i]
                            if field:  # Skip empty field names
                                result[field] = value
                        else:
                            # Excess values get synthetic field names
                            result[f"extra_field_{i-len(fieldnames)+1}"] = value

                    if result:  # Only yield non-empty dictionaries
                        yield result
                        count += 1

                    if limit_rows is not None and count >= limit_rows:
                        break
            except Exception as e:
                # If CSV parsing fails, try simple splitting as fallback
                parts = line.split(delimiter)
                result = {}
                for i, part in enumerate(parts):
                    if i < len(fieldnames):
                        field = fieldnames[i]
                        result[field] = part.strip() if field else f"field_{i}"
                    else:
                        result[f"field_{i}"] = part.strip()

                if result:
                    yield result
                    count += 1

                if limit_rows is not None and count >= limit_rows:
                    break

    except Exception as e:
        print(f"Error in CSV streaming: {e}. Using basic fallback.")
        # Last resort fallback - stream line by line with minimal processing
        all_lines = chain(sample_lines, lines_gen)
        count = 0

        # Skip the header line which we already used
        next(all_lines, None)

        for line in all_lines:
            if line.strip():
                # Use simple splitting for maximum compatibility
                result = {"raw_line": line}
                parts = line.split(",") if "," in line else line.split(delimiter)

                for i, part in enumerate(parts):
                    result[f"field_{i}"] = part.strip()

                if result:
                    yield result
                    count += 1

                if limit_rows is not None and count >= limit_rows:
                    break


def stream_csv_feed(
    response: requests.Response,
    limit_rows: Optional[int] = None,
    max_field_length: Optional[int] = None,
    decompress_type: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """Stream CSV from HTTP response with optional decompression."""
    try:
        if decompress_type == "zip":
            # Read entire ZIP into memory (zipfile requires random access).
            content = response.content
            with zipfile.ZipFile(io.BytesIO(content), "r") as z:
                for name in z.namelist():
                    if not name.lower().endswith(".csv"):
                        continue

                    with z.open(name, "r") as csv_file:
                        lines_gen = (
                            line.decode("utf-8", errors="replace") for line in csv_file
                        )
                        yield from stream_csv_lines(
                            lines_gen, limit_rows, max_field_length
                        )

        elif decompress_type == "gz":
            # Wrap response.raw in a GzipFile
            gz = gzip.GzipFile(fileobj=response.raw)
            lines_gen = (line.decode("utf-8", errors="replace") for line in gz)
            yield from stream_csv_lines(lines_gen, limit_rows, max_field_length)

        elif decompress_type == "bz2":
            bz = bz2.BZ2File(response.raw)
            lines_gen = (line.decode("utf-8", errors="replace") for line in bz)
            yield from stream_csv_lines(lines_gen, limit_rows, max_field_length)

        else:
            # No compression or unsupported format => treat as plaintext
            lines_gen = response.iter_lines(decode_unicode=True)
            yield from stream_csv_lines(lines_gen, limit_rows, max_field_length)

    finally:
        response.close()
