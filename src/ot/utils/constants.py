from pathlib import Path

# Constants for One Thing application

# Directory to store cached data
CACHE_DIR = Path.home() / ".one_thing"

# Version of the state file format
STATE_VERSION = 2

# Name of the state file
STATE_FILE = "one_thing.json"

# Date format constants
DATE_FORMAT = "%Y-%m-%d"

MONTH_FORMAT = "%Y-%m"
