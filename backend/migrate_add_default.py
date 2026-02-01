#!/usr/bin/env python3
"""Migration script to add is_default column to lists table."""

import sqlite3
import os

DB_PATH = os.path.join(os.environ.get("DB_DIR", "/app/data"), "shopping.db")

def migrate():
    """Add is_default column to lists table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if is_default column exists
    cursor.execute("PRAGMA table_info(lists)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'is_default' not in columns:
        print("Adding 'is_default' column to lists table...")
        cursor.execute("ALTER TABLE lists ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("✓ is_default column added successfully!")
    else:
        print("✓ is_default column already exists")

    # Check how many lists exist
    cursor.execute("SELECT COUNT(*) FROM lists")
    count = cursor.fetchone()[0]
    print(f"\nCurrent database has {count} list(s)")

    # If exactly one list exists, make it default for convenience
    if count == 1:
        cursor.execute("SELECT id, name FROM lists")
        list_data = cursor.fetchone()
        print(f"Setting '{list_data[1]}' as default...")
        cursor.execute("UPDATE lists SET is_default = 1 WHERE id = ?", (list_data[0],))
        conn.commit()
        print("✓ Default list set!")

    conn.close()

if __name__ == "__main__":
    migrate()
