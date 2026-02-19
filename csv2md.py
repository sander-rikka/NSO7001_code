#!/usr/bin/env python3
import csv
import sys

def md_escape(cell: str) -> str:
    """
    Minimal escaping for Markdown tables:
    - replace newlines with spaces
    - escape pipe characters so they don't break the table
    """
    cell = "" if cell is None else str(cell)
    cell = cell.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    cell = cell.replace("|", r"\|")
    return cell.strip()

def csv_to_markdown(csv_path: str) -> str:
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return ""

    header = rows[0]
    body = rows[1:]

    header_md = "| " + " | ".join(md_escape(h) for h in header) + " |"
    sep_md = "| " + " | ".join("---" for _ in header) + " |"

    body_md_lines = []
    for row in body:
        # pad short rows so the number of cells matches the header
        row = row + [""] * (len(header) - len(row))
        body_md_lines.append("| " + " | ".join(md_escape(c) for c in row[:len(header)]) + " |")

    return "\n".join([header_md, sep_md] + body_md_lines)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python csv_to_md.py input.csv", file=sys.stderr)
        sys.exit(1)

    print(csv_to_markdown(sys.argv[1]))
