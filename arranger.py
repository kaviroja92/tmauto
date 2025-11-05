# arranger.py
import aiosqlite
import logging
from collections import defaultdict
from db import init_db

logger = logging.getLogger('arranger')

async def build_groups(db_path='tmauto.db'):
    db = await aiosqlite.connect(db_path)
    cur = await db.execute('SELECT group_tag, msg_id, file_name, file_size, date_utc, title, year, season, episode, languages FROM files ORDER BY group_tag, date_utc')
    rows = await cur.fetchall()
    groups = defaultdict(list)
    for r in rows:
        tag = r[0]
        groups[tag].append({
            'msg_id': r[1],
            'file_name': r[2],
            'file_size': r[3],
            'date_utc': r[4],
            'title': r[5],
            'year': r[6],
            'season': r[7],
            'episode': r[8],
            'languages': r[9]
        })
    await db.close()
    return groups

# Example usage:
# import asyncio
# from arranger import build_groups
# groups = asyncio.run(build_groups())
# for tag, items in groups.items(): print(tag, len(items))