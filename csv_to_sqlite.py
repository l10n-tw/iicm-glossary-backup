#!/usr/bin/env python3
"""
Convert IICM glossary CSV files to SQLite database
"""
import csv
import sqlite3
from pathlib import Path
import re


def extract_letter_from_filename(filename: str) -> str:
    """
    Extract letter from filename
    Example: termb_B.csv -> 'B', termb_0.csv -> '0'
    """
    # Match character after termb_ (letter or digit)
    match = re.search(r'termb_([A-Z0-9])\.csv', filename)
    if match:
        return match.group(1)
    
    raise ValueError(f"Cannot extract letter from filename: {filename}")


def create_database(db_path: Path):
    """
    Create SQLite database and table structure
    
    Args:
        db_path: Database file path
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS glossary (
            letter CHAR(1) NOT NULL,
            id INTEGER NOT NULL,
            term VARCHAR(255),
            term_tw VARCHAR(255),
            term_cn VARCHAR(255),
            term_other VARCHAR(255),
            PRIMARY KEY (letter, id)
        )
    """)
    
    # Create indexes to improve query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_id ON glossary(id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_letter ON glossary(letter)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_term ON glossary(term)")
    
    conn.commit()
    conn.close()
    print(f"Database created: {db_path}")


def import_csv_to_db(csv_file: Path, db_path: Path, letter: str):
    """
    Import CSV file to database
    
    Args:
        csv_file: CSV file path
        db_path: Database file path
        letter: Letter identifier
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    skipped_count = 0
    
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Parse CSV row
                id_value = int(row["編號"])
                term = row["原文"].strip() if row["原文"] else None
                term_tw = row["臺灣用語"].strip() if row["臺灣用語"] else None
                term_cn = row["大陸用語"].strip() if row["大陸用語"] else None
                term_other = row["其他用語"].strip() if row["其他用語"] else None
                
                # Insert data (using INSERT OR REPLACE to handle duplicate keys)
                cursor.execute("""
                    INSERT OR REPLACE INTO glossary 
                    (letter, id, term, term_tw, term_cn, term_other)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (letter, id_value, term, term_tw, term_cn, term_other))
                
                inserted_count += 1
                
            except (ValueError, KeyError) as e:
                print(f"  Warning: Skipping invalid row: {row} - {e}")
                skipped_count += 1
                continue
    
    conn.commit()
    conn.close()
    
    print(f"  {csv_file.name}: Inserted {inserted_count} records, skipped {skipped_count} records")


def main():
    # Set paths
    csv_dir = Path("artifacts/iicm-glossary-csv")
    db_path = Path("artifacts/iicm_glossary.db")
    
    # Check if CSV directory exists
    if not csv_dir.exists():
        print(f"Error: Directory not found {csv_dir}")
        return
    
    # Create database
    print("Creating database...")
    create_database(db_path)
    
    # Process all CSV files
    csv_files = sorted(csv_dir.glob("termb_*.csv"))
    
    if not csv_files:
        print(f"Error: No CSV files found in {csv_dir}")
        return
    
    print(f"\nFound {len(csv_files)} CSV files, starting import...")
    
    for csv_file in csv_files:
        letter = extract_letter_from_filename(csv_file.name)
        
        if letter is None:
            print(f"  Warning: Cannot extract letter from filename: {csv_file.name}")
            continue
        
        print(f"Processing {csv_file.name} (letter: {letter})...")
        import_csv_to_db(csv_file, db_path, letter)
    
    # Display statistics
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM glossary")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT letter) FROM glossary")
    letter_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("\nImport completed!")
    print(f"Total records: {total_count}")
    print(f"Number of letters: {letter_count}")
    print(f"Database location: {db_path.absolute()}")


if __name__ == "__main__":
    main()
