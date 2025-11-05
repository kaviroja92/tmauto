# db.py
import aiosqlite
from datetime import datetime
import config

DB_PATH = config.DB_PATH

async def init_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        msg_id TEXT UNIQUE,
        chat_id INTEGER,
        message_id INTEGER,
        file_name TEXT,
        file_size INTEGER,
        date_utc TEXT,
        title TEXT,
        year INTEGER,
        season INTEGER,
        episode TEXT,
        languages TEXT,
        quality TEXT,
        group_tag TEXT,
        parsed_at TEXT
    )
    ''')
    await db.execute('''
    CREATE TABLE IF NOT EXISTS checkpoints (
        name TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    await db.commit()
    return db

async def set_checkpoint(db, name, value):
    await db.execute('INSERT OR REPLACE INTO checkpoints (name, value) VALUES (?, ?)', (name, value))
    await db.commit()

async def get_checkpoint(db, name):
    cur = await db.execute('SELECT value FROM checkpoints WHERE name = ?', (name,))
    row = await cur.fetchone()
    return row[0] if row else None

def msg_key(chat_id, message_id):
    return f"{chat_id}:{message_id}"