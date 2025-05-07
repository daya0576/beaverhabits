import nicegui
from nicegui import ui

from beaverhabits.logger import logger
from fly.memory import MemoryMonitor

# Debug memory usage
hourly_monitor = MemoryMonitor("Hourly monitor", total_threshold=10, diff_threshold=-1)
ui.timer(60 * 60, hourly_monitor.print_stats)


# Clear session storage memory cache
def clear_storage():
    logger.info("Clearing session storage cache")
    nicegui.app.storage._users.clear()


ui.timer(60 * 60 * 24, clear_storage)
