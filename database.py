import sqlite3
import os


def setup_database():
    # Create database file if it doesn't exist
    database_exists = os.path.exists('feedback.db')

    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()

    if not database_exists:
        # Create raw feedback table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_feedback (
            post_id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            source TEXT,
            date TEXT,
            url TEXT
        )
        ''')

        # Create analyzed feedback table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyzed_feedback (
            feedback_id TEXT PRIMARY KEY,
            theme TEXT,
            sentiment TEXT,
            summary TEXT,
            source_id TEXT,
            FOREIGN KEY (source_id) REFERENCES raw_feedback (post_id)
        )
        ''')

        # Create ideas table with additional fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ideas (
            idea_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            votes INTEGER DEFAULT 0,
            status TEXT,
            created_date TEXT,
            last_updated TEXT
        )
        ''')

        print("Base tables created successfully!")

    # Always try to create the new tables regardless of whether the DB exists

    # Check if notifications table exists and create if it doesn't
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'")
    if not cursor.fetchone():
        # Create notifications table
        cursor.execute('''
        CREATE TABLE notifications (
            notification_id TEXT PRIMARY KEY,
            feedback_id TEXT,
            idea_id TEXT,
            message TEXT,
            status TEXT,
            created_date TEXT,
            sent_date TEXT,
            FOREIGN KEY (feedback_id) REFERENCES raw_feedback (post_id),
            FOREIGN KEY (idea_id) REFERENCES ideas (idea_id)
        )
        ''')
        print("Added notifications table.")

    # Check if feedback_idea_map table exists and create if it doesn't
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_idea_map'")
    if not cursor.fetchone():
        # Create feedback_idea_map table
        cursor.execute('''
        CREATE TABLE feedback_idea_map (
            feedback_id TEXT,
            idea_id TEXT,
            PRIMARY KEY (feedback_id, idea_id),
            FOREIGN KEY (feedback_id) REFERENCES raw_feedback (post_id),
            FOREIGN KEY (idea_id) REFERENCES ideas (idea_id)
        )
        ''')
        print("Added feedback_idea_map table.")

    # Check if ideas table has the new columns
    cursor.execute("PRAGMA table_info(ideas)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    # Add missing columns to ideas table if needed
    if "created_date" not in column_names:
        cursor.execute("ALTER TABLE ideas ADD COLUMN created_date TEXT")
        print("Added created_date column to ideas table.")

    if "last_updated" not in column_names:
        cursor.execute("ALTER TABLE ideas ADD COLUMN last_updated TEXT")
        print("Added last_updated column to ideas table.")

    conn.commit()
    conn.close()
    print("Database schema updated!")


if __name__ == "__main__":
    setup_database()