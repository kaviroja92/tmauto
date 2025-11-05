# poster.py
import asyncio
import logging
from telethon.tl.types import InputPeerChannel
from telethon.errors import FloodWaitError

import config
from telethon_client import make_client
from db import init_db

logger = logging.getLogger('poster')

async def copy_group_to_arranged(group_items, dry_run=False):
    # group_items: list of dicts with 'msg_id' (chat:msg)
    client = make_client()
    await client.start()
    dst = config.ARRANGE_CHANNEL
    # posting rate limits
    interval = config.POSTING_MIN_INTERVAL
    burst = config.POSTING_BURST
    long_sleep = config.POSTING_LONG_SLEEP

    count = 0
    for it in group_items:
        msg_key = it['msg_id']
        parts = msg_key.split(':')
        chat_id = int(parts[0])
        msg_id = int(parts[1])
        try:
            if dry_run:
                logger.info('[dry] would copy %s -> %s', msg_key, dst)
            else:
                await client.copy_message(dst, chat_id, msg_id)
                logger.info('Copied %s -> %s', msg_key, dst)
        except FloodWaitError as e:
            logger.warning('FloodWait %s sec encountered; sleeping', e.seconds)
            await asyncio.sleep(e.seconds + 1)
            await client.copy_message(dst, chat_id, msg_id)
        count += 1
        if count % burst == 0:
            await asyncio.sleep(long_sleep)
        else:
            await asyncio.sleep(interval)
    await client.disconnect()

async def delete_existing_group_on_arranged(example_tag, dry_run=False):
    # This is a placeholder: to detect existing group in arranged channel we need to identify the header message.
    # Implementation depends on header format; for now we won't auto-delete; poster will post full group.
    return