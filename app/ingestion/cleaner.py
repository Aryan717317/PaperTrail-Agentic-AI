"""
app/ingestion/cleaner.py

Cleans raw text extracted from PDF pages before chunking.

What it does
------------
1. Collapses runs of blank lines to a single blank line.
2. Removes lines that look like page numbers or running headers/footers
   (very short lines containing only digits, roman numerals, or common header
   words).
3. Strips leading/trailing whitespace from each line.
4. Collapses runs of spaces within a line to a single space.

What it deliberately does NOT do
---------------------------------
- It does not parse tables or figures (future work).
- It does not handle multi-column reflow (future work).
- It does not use any ML model; it is entirely heuristic.
"""

import re


# Lines shorter than this threshold that match the header/footer pattern
# are removed. Raise this value to be more aggressive, lower it to be
# more conservative.
_SHORT_LINE_MAX = 60
_PAGE_NUMBER_RE = re.compile(
    r"^\s*"
    r"(?:"
    r"\d{1,4}"                        # bare page number
    r"|[ivxlcdmIVXLCDM]{1,10}"       # roman numerals
    r"|(?:page|p\.?)\s*\d+"          # "Page 4" / "p. 4"
    r"|(?:chapter|section)\s*\d+"    # "Chapter 2"
    r")"
    r"\s*$",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r" {2,}")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """
    Apply heuristic cleaning to a single page's extracted text.

    Parameters
    ----------
    text : str
        Raw text as returned by PyMuPDF.

    Returns
    -------
    str
        Cleaned text.  Returns an empty string if nothing meaningful survives.
    """
    lines = text.splitlines()
    cleaned: list[str] = []

    for line in lines:
        line = line.strip()
        line = _MULTI_SPACE_RE.sub(" ", line)

        # Drop very short lines that look like page numbers / headers.
        if len(line) < _SHORT_LINE_MAX and _PAGE_NUMBER_RE.match(line):
            continue

        cleaned.append(line)

    result = "\n".join(cleaned)
    # Collapse triple+ blank lines to double.
    result = _MULTI_NEWLINE_RE.sub("\n\n", result)
    return result.strip()

