# telethon_client.py
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
import config

logger = logging.getLogger("telethon_client")

def make_client():
    if config.SESSION_STRING and config.SESSION_STRING.strip():
        return TelegramClient(StringSession(config.SESSION_STRING), config.API_ID, config.API_HASH)
    return TelegramClient('tmauto', config.API_ID, config.API_HASH)