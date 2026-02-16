import sqlite3
import os

def migrate():
    db_path = os.path.join(os.getcwd(), 'healthcare.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if consultation_fee column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'consultation_fee' not in columns:
            print("Adding 'consultation_fee' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN consultation_fee FLOAT DEFAULT 0.0")
            print("Column added successfully.")
        else:
            print("'consultation_fee' column already exists.")

        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
