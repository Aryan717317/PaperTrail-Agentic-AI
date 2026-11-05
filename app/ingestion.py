import fitz


def extract_pages(pdf_path: str, filename: str) -> tuple[str, list[dict]]:
    from uuid import uuid4

    paper_id = str(uuid4())
    pages = []

    with fitz.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append({
                    "paper_id": paper_id,
                    "filename": filename,
                    "page": page_number,
                    "text": text,
                })

    if not pages:
        raise ValueError(
            "No selectable text was found. This may be a scanned PDF; OCR is not included yet."
        )
    return paper_id, pages


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1200,
    overlap: int = 180,
) -> list[dict]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0.")

    chunks = []
    for page in pages:
        text = page.get("text", "")
        if not isinstance(text, str):
            raise ValueError("Each page must contain text as a string.")
        if not text.strip():
            continue

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            content = text[start:end].strip()
            if content:
                chunks.append({
                    "text": content,
                    "metadata": {
                        "paper_id": page["paper_id"],
                        "filename": page["filename"],
                        "page": int(page["page"]),
                    },
                })
            if end >= len(text):
                break
            start = end - overlap
    return chunks
