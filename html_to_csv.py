#!/usr/bin/env python3
"""
Convert IICM glossary HTML files to CSV format
"""
import csv
import html
from pathlib import Path
from selectolax.parser import HTMLParser


def clean_text(text: str) -> str:
    """Clean text: remove HTML entities and whitespace"""
    # Decode HTML entities (e.g., &nbsp;)
    text = html.unescape(text)
    # Remove extra whitespace
    text = text.strip()
    return text


def parse_html_to_csv(html_file: Path, csv_file: Path):
    """
    Parse HTML file and convert to CSV
    
    Args:
        html_file: Input HTML file path
        csv_file: Output CSV file path
    """
    # Read HTML file
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Parse HTML using selectolax
    parser = HTMLParser(html_content)
    
    # Find table
    table = parser.css_first("table")
    if not table:
        raise ValueError("Table element not found")
    
    # Prepare CSV writing
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        
        # Write header
        header = ["編號", "原文", "臺灣用語", "大陸用語", "其他用語"]
        writer.writerow(header)
        
        # Find all data rows (skip header row)
        rows = table.css("tr")
        
        for row in rows:
            # Get all td elements in this row
            cells = row.css("td")
            
            # Skip header row (header row td usually has align="center" attribute)
            if len(cells) == 0:
                continue
            
            # Check if it's a header row (first td content is "編號")
            first_cell_text = clean_text(cells[0].text())
            if first_cell_text == "編號":
                continue
            
            # Extract first 5 columns of data (ignore 6th column link)
            if len(cells) >= 5:
                row_data = [
                    clean_text(cells[0].text()),  # 編號
                    clean_text(cells[1].text()),  # 原文
                    clean_text(cells[2].text()),  # 臺灣用語
                    clean_text(cells[3].text()),  # 大陸用語
                    clean_text(cells[4].text()),  # 其他用語
                ]
                writer.writerow(row_data)


def main():
    # read files in iicm-glossary directory
    files = Path("iicm-glossary").glob("*.htm")
    output_dir = Path("iicm-glossary-csv")
    output_dir.mkdir(exist_ok=True)

    for file in files:
        print(f"Processing {file}...")
        parse_html_to_csv(file, output_dir / file.with_suffix(".csv").name)


if __name__ == "__main__":
    main()
