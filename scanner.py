# scanner.py
import asyncio
import logging
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from telethon.errors import FloodWaitError
from telethon.tl.types import Message

import config
from telethon_client import make_client
from db import init_db, set_checkpoint, get_checkpoint
from parser import parse_filename

logger = logging.getLogger('scanner')

async def get_title_of_message(msg: Message):
    fn = None
    if getattr(msg, 'caption', None):
        fn = msg.caption
    else:
        if getattr(msg, 'document', None) and getattr(msg.document, 'file_name', None):
            fn = msg.document.file_name
        elif getattr(msg, 'video', None) and getattr(msg.video, 'file_name', None):
            fn = msg.video.file_name
        elif getattr(msg, 'audio', None) and getattr(msg.audio, 'file_name', None):
            fn = msg.audio.file_name
    if not fn:
        return None, None
    meta = parse_filename(fn)
    return fn, meta


def yesterday_cutoff(cfg):
    tz = ZoneInfo(cfg.get('TIMEZONE', 'Asia/Kolkata'))
    now = datetime.now(tz)
    y = (now - timedelta(days=1)).date()
    cutoff = datetime.combine(y, time(23, 59, 59))
    cutoff = cutoff.replace(tzinfo=tz)
    return cutoff


async def scan_initial_or_incremental(full_scan=False):
    cfg = config
    client = make_client()
    db = await init_db()
    await client.start()
    dump = cfg.DUMP_CHANNEL
    batch = cfg.SCAN_BATCH_SIZE
    sleep_between = cfg.SCAN_SLEEP_SECONDS
    tz = ZoneInfo(cfg.TIMEZONE)
    cutoff = yesterday_cutoff(cfg)

    logger.info('Starting scan; cutoff (IST): %s', cutoff.isoformat())
    # find newest message id
    try:
        newest = await client.get_messages(dump, limit=1)
        newest_id = newest[0].id if newest else None
    except FloodWaitError as e:
        logger.warning('FloodWait fetching newest: %s', e.seconds)
        await asyncio.sleep(e.seconds + 1)
        newest = await client.get_messages(dump, limit=1)
        newest_id = newest[0].id if newest else None

    if newest_id is None:
        logger.info('Dump channel empty or not accessible')
        await client.disconnect()
        await db.close()
        return

    # walk backwards until we find last message <= cutoff
    current = newest_id
    last_msg_before_cutoff = None
    while True:
        msgs = await client.get_messages(dump, limit=batch, offset_id=current)
        if not msgs:
            break
        for m in msgs:
            if not getattr(m, 'media', None):
                continue
            mdate = m.date.astimezone(tz)
            if mdate <= cutoff:
                last_msg_before_cutoff = m
                break
        if last_msg_before_cutoff:
            break
        # go older
        current = msgs[-1].id - 1
        await asyncio.sleep(sleep_between)
        if current <= 0:
            break

    if not last_msg_before_cutoff:
        logger.info('No message found before cutoff; nothing to scan')
        await client.disconnect()
        await db.close()
        return

    fn, meta = await get_title_of_message(last_msg_before_cutoff)
    last_title_tag = meta['group_tag'] if meta else None
    logger.info('Last message before cutoff id=%s title=%s', last_msg_before_cutoff.id, last_title_tag)

    # iterate oldest->newest and include messages <= cutoff OR same title cluster
    collected = []
    seen_after_cutoff_with_last_tag = False
    async for m in client.iter_messages(dump, reverse=True):
        if not getattr(m, 'media', None):
            continue
        fn, meta = await get_title_of_message(m)
        if not meta:
            continue
        tag = meta.get('group_tag')
        mdate = m.date.astimezone(tz)
        include = False
        if mdate <= cutoff:
            include = True
        else:
            if last_title_tag and tag == last_title_tag:
                include = True
                seen_after_cutoff_with_last_tag = True
            else:
                include = False
        if include:
            key = f"{m.chat_id}:{m.id}"
            cur = await db.execute('SELECT 1 FROM files WHERE msg_id = ?', (key,))
            row = await cur.fetchone()
            if not row:
                await db.execute('INSERT INTO files (msg_id, chat_id, message_id, file_name, file_size, date_utc, title, year, season, episode, languages, quality, group_tag, parsed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                    key,
                    m.chat_id,
                    m.id,
                    fn,
                    (m.document.file_size if getattr(m, 'document', None) else (m.video.file_size if getattr(m, 'video', None) else None)),
                    m.date.isoformat(),
                    meta.get('title'),
                    meta.get('year'),
                    meta.get('season'),
                    meta.get('episode'),
                    meta.get('languages'),
                    meta.get('quality'),
                    meta.get('group_tag'),
                    datetime.utcnow().isoformat()
                ))
                await db.commit()
                collected.append(key)
        # stop rule: if mdate > cutoff and we've already seen last_tag posts after cutoff and current tag != last_tag, break
        if m.date.astimezone(tz) > cutoff and seen_after_cutoff_with_last_tag and tag != last_title_tag:
            break

    if collected:
        await set_checkpoint(db, 'last_scanned_msg', collected[-1])
        logger.info('Collected %d new entries', len(collected))
    else:
        logger.info('No new entries found')

    await client.disconnect()
    await db.close()