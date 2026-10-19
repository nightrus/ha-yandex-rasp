"""Constants for the Yandex Rasp integration."""

from typing import Final

DOMAIN: Final = "yandex_rasp"
VERSION: Final = "0.1.0"

API_URL: Final = "https://api.rasp.yandex.net/v3.0/schedule/"
API_PAGE_LIMIT: Final = 100

CONF_STATION: Final = "station"
CONF_UPDATE_INTERVAL: Final = "update_interval"

DEFAULT_STATION: Final = "s9601805"  # Бескудниково
DEFAULT_UPDATE_INTERVAL: Final = 30  # minutes
MIN_UPDATE_INTERVAL: Final = 15  # 500 requests/day free quota
MAX_UPDATE_INTERVAL: Final = 1440

# How far ahead departures are exposed in sensor attributes; the card
# narrows this down to its own window (1 hour by default).
ATTR_WINDOW_HOURS: Final = 3

# Directions containing this word are listed first.
PRIORITY_DIRECTION: Final = "москв"

CARD_URL: Final = "/yandex_rasp/yandex-rasp-card.js"
