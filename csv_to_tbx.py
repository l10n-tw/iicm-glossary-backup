#!/usr/bin/env python3
"""
Convert IICM glossary CSV files to TermBase Exchange (TBX) format
"""

import csv
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


ARTIFACT_DIR = Path("artifacts")


def escape_xml_text(text: str) -> str:
    """Escape XML special characters"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def create_tbx_document():
    """Create TBX document structure"""
    # Register XML namespace prefix
    ET.register_namespace("", "")
    
    # Create root element
    martif = ET.Element("martif", type="TBX")
    martif.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
    
    # Create header
    martif_header = ET.SubElement(martif, "martifHeader")
    file_desc = ET.SubElement(martif_header, "fileDesc")
    source_desc = ET.SubElement(file_desc, "sourceDesc")
    p = ET.SubElement(source_desc, "p")
    p.text = "IICM Glossary"
    
    # Create text body
    text = ET.SubElement(martif, "text")
    body = ET.SubElement(text, "body")
    
    return martif, body


def create_term_entry(body: ET.Element, letter: str, term_id: str, english_term: str, taiwan_term: str | None = None, mainland_term: str | None = None, other_term: str | None = None):
    """Create a termEntry element"""
    term_entry = ET.SubElement(body, "termEntry")
    
    # Add ID if provided
    term_entry.set("id", f"term-{letter}-{term_id}")
    
    # English term
    if english_term:
        lang_set_en = ET.SubElement(term_entry, "langSet")
        lang_set_en.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
        tig_en = ET.SubElement(lang_set_en, "tig")
        term_en = ET.SubElement(tig_en, "term")
        term_en.text = escape_xml_text(english_term)
    
    # Taiwan term (Traditional Chinese)
    lang_set_tw = ET.SubElement(term_entry, "langSet")
    lang_set_tw.set("{http://www.w3.org/XML/1998/namespace}lang", "zh_TW")
    tig_tw = ET.SubElement(lang_set_tw, "tig")
    term_tw = ET.SubElement(tig_tw, "term")
    if taiwan_term:
        term_tw.text = escape_xml_text(taiwan_term)
    
    # Mainland term (Simplified Chinese)
    if mainland_term:
        lang_set_cn = ET.SubElement(term_entry, "langSet")
        lang_set_cn.set("{http://www.w3.org/XML/1998/namespace}lang", "zh_Hans")
        tig_cn = ET.SubElement(lang_set_cn, "tig")
        term_cn = ET.SubElement(tig_cn, "term")
        term_cn.text = escape_xml_text(mainland_term)
    
    # Other terms as note if provided
    if other_term:
        note = ET.SubElement(term_entry, "note", attrib={"from": "translator"})
        note.text = escape_xml_text(f"其他用語: {other_term}")


def process_csv_files(csv_dir: Path, output_file: Path):
    """Process all CSV files and create TBX document"""
    # Create TBX document structure
    martif, body = create_tbx_document()
    
    # Get all CSV files
    csv_files = sorted(csv_dir.glob("termb_*.csv"))
    
    if not csv_files:
        print(f"Error: No CSV files found in {csv_dir}")
        return
    
    print(f"Found {len(csv_files)} CSV files, processing...")
    
    total_entries = 0
    
    for csv_file in csv_files:
        print(f"Processing {csv_file.name}...")
        entry_count = 0
        
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse CSV row
                    letter = csv_file.stem.replace("termb_", "")
                    term_id = row["編號"].strip() if row["編號"] else None
                    english_term = row["原文"].strip() if row["原文"] else None
                    taiwan_term = row["臺灣用語"].strip() if row["臺灣用語"] else None
                    mainland_term = row["大陸用語"].strip() if row["大陸用語"] else None
                    other_term = row["其他用語"].strip() if row["其他用語"] else None
                    
                    # Skip if no English term
                    if not english_term:
                        continue

                    assert term_id is not None
                    
                    # Create term entry
                    create_term_entry(
                        body,
                        letter=letter,
                        term_id=term_id,
                        english_term=english_term,
                        taiwan_term=taiwan_term if taiwan_term else None,
                        mainland_term=mainland_term if mainland_term else None,
                        other_term=other_term if other_term else None,
                    )
                    
                    entry_count += 1
                    total_entries += 1
                    
                except (KeyError, ValueError) as e:
                    print(f"  Warning: Skipping invalid row: {row} - {e}")
                    continue
        
        print(f"  {csv_file.name}: Added {entry_count} entries")
    
    # Convert to XML string
    xml_string = ET.tostring(martif, encoding="unicode")
    
    # Parse with minidom for pretty printing
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="    ", encoding=None)
    
    # Add DOCTYPE declaration
    doctype = '<!DOCTYPE martif PUBLIC "ISO 12200:1999A//DTD MARTIF core (DXFcdV04)//EN" "TBXcdv04.dtd">'
    
    # Process the XML to add DOCTYPE and fix namespace prefixes
    lines = pretty_xml.split('\n')
    output_lines = []
    
    for i, line in enumerate(lines):
        # Replace XML declaration
        if line.strip().startswith('<?xml'):
            output_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
            output_lines.append('')
            output_lines.append(doctype)
        # Fix xml:lang namespace (replace {http://www.w3.org/XML/1998/namespace}lang with xml:lang)
        elif '{http://www.w3.org/XML/1998/namespace}lang' in line:
            line = line.replace('{http://www.w3.org/XML/1998/namespace}lang', 'xml:lang')
            output_lines.append(line)
        else:
            output_lines.append(line)
    
    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('\n'.join(output_lines))
    
    print("\nConversion completed!")
    print(f"Total entries: {total_entries}")
    print(f"Output file: {output_file.absolute()}")


def main():
    # Set paths
    csv_dir = ARTIFACT_DIR / "iicm-glossary-csv"
    output_file = ARTIFACT_DIR / "iicm_glossary.tbx"
    
    # Check if CSV directory exists
    if not csv_dir.exists():
        print(f"Error: Directory not found {csv_dir}")
        return
    
    # Process CSV files and create TBX file
    process_csv_files(csv_dir, output_file)


if __name__ == "__main__":
    main()
