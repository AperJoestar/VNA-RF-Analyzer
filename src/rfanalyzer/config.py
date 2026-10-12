"""Application-wide constants and file locations."""
import os

APP_NAME = "RF Analyzer"

# Output folders are created relative to the working directory, next to the CSV logs being analysed.
EXPORTS_DIR = "exports"
PICS_DIR = "Pics"

# The chosen theme is remembered per user. Override the location with the RF_ANALYZER_SETTINGS env variable.
SETTINGS_FILE = os.environ.get("RF_ANALYZER_SETTINGS") or os.path.join(
    os.path.expanduser("~"), ".rf_analyzer", "settings.json"
)
