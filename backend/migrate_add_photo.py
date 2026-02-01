#!/usr/bin/env python3
"""Migration script to add photo column to recipes table."""

import sqlite3
import os

DB_PATH = os.path.join(os.environ.get("DB_DIR", "/app/data"), "shopping.db")

def migrate():
    """Add photo column to recipes table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if photo column exists
    cursor.execute("PRAGMA table_info(recipes)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'photo' not in columns:
        print("Adding 'photo' column to recipes table...")
        cursor.execute("ALTER TABLE recipes ADD COLUMN photo TEXT DEFAULT NULL")
        conn.commit()
        print("✓ Photo column added successfully!")
    else:
        print("✓ Photo column already exists")

    # Check if there are any recipes
    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()[0]
    print(f"\nCurrent database has {count} recipe(s)")

    conn.close()

if __name__ == "__main__":
    migrate()
