"""
PDF content extractor using pdfplumber.
Optimized for Power BI reports containing tables and numerical data.
"""

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


def extract_pdf_content(pdf_path: Path) -> str:
    """
    Extract all text and tables from a PDF file.

    Returns a structured string with all content organized by page,
    with tables formatted as readable ASCII tables.
    """
    logger.info(f"Extracting content from: {pdf_path.name}")

    all_content: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"PDF has {total_pages} page(s)")

        for page_num, page in enumerate(pdf.pages, start=1):
            page_content: list[str] = []
            page_content.append(f"\n{'='*60}")
            page_content.append(f"PAGE {page_num} OF {total_pages}")
            page_content.append(f"{'='*60}\n")

            # Extract tables first (more structured data)
            tables = page.extract_tables()
            if tables:
                for table_idx, table in enumerate(tables, start=1):
                    page_content.append(f"--- Table {table_idx} ---")
                    formatted = _format_table(table)
                    page_content.append(formatted)
                    page_content.append("")

            # Also extract full page text for any content outside tables
            text = page.extract_text()
            if text:
                # Remove text that's already captured in tables to avoid duplication
                page_content.append("--- Text Content ---")
                page_content.append(text.strip())
                page_content.append("")

            all_content.append("\n".join(page_content))

    full_content = "\n".join(all_content)
    logger.info(
        f"Extraction complete: {total_pages} page(s), "
        f"{len(full_content):,} characters"
    )
    return full_content


def _format_table(table: list[list]) -> str:
    """
    Format a table (list of rows) into a readable ASCII table.
    Handles None values and varying column widths.
    """
    if not table:
        return "(empty table)"

    # Clean up cell values
    cleaned = []
    for row in table:
        cleaned_row = [
            str(cell).strip() if cell is not None else ""
            for cell in row
        ]
        cleaned.append(cleaned_row)

    # Normalize row lengths
    max_cols = max(len(row) for row in cleaned)
    for row in cleaned:
        while len(row) < max_cols:
            row.append("")

    # Calculate column widths
    col_widths = []
    for col_idx in range(max_cols):
        max_width = max(
            len(row[col_idx]) for row in cleaned
        )
        col_widths.append(min(max_width, 40))  # Cap at 40 chars

    # Build formatted table
    lines = []
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    for row_idx, row in enumerate(cleaned):
        cells = []
        for col_idx, cell in enumerate(row):
            width = col_widths[col_idx]
            cells.append(f" {cell:<{width}} ")
        line = "|" + "|".join(cells) + "|"
        lines.append(line)

        # Add separator after header row
        if row_idx == 0:
            lines.insert(0, separator)
            lines.append(separator)

    lines.append(separator)
    return "\n".join(lines)


def extract_summary_stats(pdf_path: Path) -> dict:
    """
    Extract basic stats about the PDF for logging/debugging.
    """
    stats = {
        "file_name": pdf_path.name,
        "file_size_kb": round(pdf_path.stat().st_size / 1024, 1),
        "total_pages": 0,
        "total_tables": 0,
        "has_text": False,
    }

    with pdfplumber.open(pdf_path) as pdf:
        stats["total_pages"] = len(pdf.pages)
        for page in pdf.pages:
            tables = page.extract_tables()
            stats["total_tables"] += len(tables)
            if page.extract_text():
                stats["has_text"] = True

    logger.info(f"PDF stats: {stats}")
    return stats
