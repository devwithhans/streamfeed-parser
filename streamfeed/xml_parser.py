import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, Iterator, List, Union, Tuple
import requests
import zipfile
import gzip
import io
import re


def strip_namespace(tag: str) -> str:
    """
    Given a string like '{http://base.google.com/ns/1.0}id',
    return just 'id'.
    """
    return re.sub(r"{.*}", "", tag)


def element_to_dict(element: ET.Element) -> Union[str, Dict[str, Any]]:
    """
    Recursively convert an ElementTree Element into a nested dictionary
    (or just a string if it's a simple text node).
    """
    # If the element has no children and only text, return the text directly:
    if not list(element) and (element.text and element.text.strip()):
        return element.text.strip()

    node_dict = {}

    # Add attributes (if any).
    if element.attrib:
        node_dict["@attributes"] = dict(element.attrib)

    # Recurse on children
    for child in element:
        child_tag = strip_namespace(child.tag)
        child_val = element_to_dict(child)

        # If a tag is repeated, store as a list
        if child_tag in node_dict:
            if not isinstance(node_dict[child_tag], list):
                node_dict[child_tag] = [node_dict[child_tag]]
            node_dict[child_tag].append(child_val)
        else:
            node_dict[child_tag] = child_val

    # If there is text in the element itself (outside children) that's non-empty
    if element.text and element.text.strip():
        # Store it under "#text"
        node_dict["#text"] = element.text.strip()

    return node_dict


def stream_xml_items_iterparse(
    file_obj, item_tag: str, limit_rows: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    stack = []
    count = 0
    for event, elem in ET.iterparse(file_obj, events=("start", "end")):
        if event == "start":
            stack.append(strip_namespace(elem.tag))
        else:  # event == "end"
            tag = stack.pop()
            if tag == item_tag and item_tag not in stack:
                yield element_to_dict(elem)
                count += 1
                elem.clear()
                if limit_rows is not None and count >= limit_rows:
                    break


def stream_xml_feed(
    response: requests.Response,
    item_tag: str = "product",
    limit_rows: Optional[int] = None,
    decompress_type: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """Stream XML from HTTP response with optional decompression using iterparse."""
    try:
        if decompress_type == "zip":
            content = response.content
            with zipfile.ZipFile(io.BytesIO(content), "r") as z:
                for name in z.namelist():
                    with z.open(name, "r") as xml_file:
                        yield from stream_xml_items_iterparse(
                            xml_file, item_tag=item_tag, limit_rows=limit_rows
                        )

        elif decompress_type == "gz":
            print("GZ")
            gz = gzip.GzipFile(fileobj=response.raw)
            yield from stream_xml_items_iterparse(
                gz, item_tag=item_tag, limit_rows=limit_rows
            )

        elif decompress_type == "bz2":
            bz = bz2.BZ2File(response.raw)
            yield from stream_xml_items_iterparse(
                bz, item_tag=item_tag, limit_rows=limit_rows
            )

        else:
            yield from stream_xml_items_iterparse(
                response.raw, item_tag=item_tag, limit_rows=limit_rows
            )

    finally:
        response.close()
