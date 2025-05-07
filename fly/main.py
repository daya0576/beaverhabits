import gc

import psutil
from fastapi import Response
from nicegui import app as nicegui_app
from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.logger import logger
from beaverhabits.main import app
from beaverhabits.utils import MemoryMonitor
from fly.plan.paddle import init_paddle_routes

METRICS_TEMPLATE = """\
# HELP rss Resident Set Size in bytes.
# TYPE rss gauge
rss {rss}
# TYPE mem_total gauge
mem_total {mem_total}
# TYPE mem_available gauge
mem_available {mem_available}
# TYPE uncollectable_count gauge
uncollectable_count {uncollectable_count}
# TYPE object_count gauge
object_count {object_count}
"""

# Debug memory usage
hourly_monitor = MemoryMonitor("Hourly monitor", total_threshold=10, diff_threshold=-1)
ui.timer(60 * 60, hourly_monitor.print_stats)


# Clear session storage memory cache
def clear_storage():
    logger.info("Clearing session storage cache")
    nicegui_app.storage._users.clear()


ui.timer(60 * 60 * 24, clear_storage)

exporter_monitor = MemoryMonitor("Exporter monitor")


@app.get("/metrics", tags=["metrics"])
def exporter():
    # Memory heap and stats
    process = psutil.Process()
    memory_info = process.memory_info()
    ram = psutil.virtual_memory()
    text = METRICS_TEMPLATE.format(
        rss=memory_info.rss,  # non-swapped physical memory a process has used
        mem_total=ram.total,  # total physical memory
        mem_available=ram.available,  # available memory
        uncollectable_count=len(gc.garbage),  # number of uncollectable objects
        object_count=len(gc.get_objects()),
    )

    exporter_monitor.print_stats()

    return Response(content=text, media_type="text/plain")


init_paddle_routes(app)

if settings.SENTRY_DSN:
    logger.info("Setting up Sentry...")
    import sentry_sdk

    sentry_sdk.init(settings.SENTRY_DSN, send_default_pii=True)
