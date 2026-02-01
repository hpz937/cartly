#!/usr/bin/env python3
"""Migration script to add notes column to recipes table."""

import sqlite3
import os

DB_PATH = os.path.join(os.environ.get("DB_DIR", "/app/data"), "shopping.db")

def migrate():
    """Add notes column to recipes table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if notes column exists
    cursor.execute("PRAGMA table_info(recipes)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'notes' not in columns:
        print("Adding 'notes' column to recipes table...")
        cursor.execute("ALTER TABLE recipes ADD COLUMN notes TEXT DEFAULT ''")
        conn.commit()
        print("✓ Notes column added successfully!")
    else:
        print("✓ Notes column already exists")

    # Check how many recipes exist
    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()[0]
    print(f"\nDatabase has {count} recipe(s)")

    conn.close()

if __name__ == "__main__":
    migrate()
