from pathlib import Path

# Directory to store cached data
CACHE_DIR = Path.home() / ".one_thing"

# Version of the state file format
STATE_VERSION = 2

# Name of the state file
STATE_FILE = "one_thing.json"

# Date format constants
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"

# Default number of days to show in logs
DEFAULT_LOG_DAYS = 7

# Default maximum number of backup files to keep
DEFAULT_MAX_BACKUP_FILES = 5
