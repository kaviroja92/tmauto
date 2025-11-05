# config.py
# TMAuto configuration - EDIT BEFORE RUNNING


API_ID = 1905 # replace with your API ID
API_HASH = "7ff6" # replace with your API HASH
SESSION_STRING = ""

# channel IDs (use -100... for private channels)
DUMP_CHANNEL = -1002358242291 # replace with your dumb channel id
ARRANGE_CHANNEL = -1003197574096


# scanning behavior
SCAN_BATCH_SIZE = 200
SCAN_SLEEP_SECONDS = 0.5
TIMEZONE = "Asia/Kolkata"


# cutoff / safety
POSTING_MIN_INTERVAL = 3 # seconds between copy_message calls
POSTING_BURST = 20 # after this many messages, take a long sleep
POSTING_LONG_SLEEP = 10 # seconds


# DB path
DB_PATH = "tmauto.db"
LOG_LEVEL = "INFO"


# limits
MAX_MESSAGES_PER_RUN = 1000000 # set high; scanner uses checkpointing


# Debug

DRY_RUN = False
