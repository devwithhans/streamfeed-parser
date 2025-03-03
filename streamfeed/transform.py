from typing import Optional, Dict, Any, Iterator, List


def explode_row(
    row: Dict[str, Any], explode_fields: List[str], divider: str = ","
) -> Iterator[Dict[str, Any]]:
    """
    Split each explode-field by `divider` and pair them by index (zip).
    This ensures that e.g. "size" and "ean" produce parallel pairs rather than a cartesian product.

    If the lists have different lengths, `zip` stops at the shortest by default.
    Or use `zip_longest` if you want to continue and fill missing fields with None.
    """
    # Split out each explode_field into a list
    splitted_lists = []
    for field in explode_fields:
        if field in row and row[field]:
            # e.g. "s,m,l" -> ["s","m","l"]
            splitted_lists.append([part.strip() for part in row[field].split(divider)])
        else:
            # If the field doesn't exist or is empty, treat it as a single-element [None]
            splitted_lists.append([None])

    # Now zip them together in parallel
    # Each iteration of zip(...) yields a tuple with 1 item per field.
    # If you want to yield as many rows as the LONGEST list, use zip_longest(*splitted_lists, fillvalue=None).
    for combo in zip(*splitted_lists):
        # Make a copy of the original row
        new_row = dict(row)
        # Insert the i-th item from each splitted list into the new row
        for field_name, value in zip(explode_fields, combo):
            new_row[field_name] = value
        yield new_row


def explode_rows(
    row_iterator: Iterator[Dict[str, Any]], feed_logic: Optional[Dict[str, Any]] = None
) -> Iterator[Dict[str, Any]]:
    """
    Wraps an iterator of rows and applies explode logic based on feed_logic.
    If feed_logic has 'explode_fields', it will 'zip' the splits across those fields by index.
    """
    if not feed_logic or "explode_fields" not in feed_logic:
        # No explode logic defined, yield rows as-is
        yield from row_iterator
    else:
        explode_fields = feed_logic["explode_fields"]
        divider = feed_logic.get("divider", ",")

        for row in row_iterator:
            yield from explode_row(row, explode_fields, divider)
