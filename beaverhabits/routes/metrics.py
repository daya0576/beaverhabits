import asyncio
import gc
import platform
import tracemalloc

import psutil
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import Response
from psutil._common import bytes2human

try:
    from beaverhabits.version import IDENTITY
except:
    IDENTITY = "unknown"

# fmt: off
try:
    from guppy import hpy; h=hpy() # type: ignore
except ImportError:
    pass
# fmt: on

router = APIRouter()


@router.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
async def health():
    loop = asyncio.get_event_loop()
    return dict(
        status="OK",
        loop=loop.__class__.__module__,
        python_version=platform.python_version(),
        identity=IDENTITY,
    )


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


@router.get("/metrics", tags=["metrics"])
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

    return Response(content=text, media_type="text/plain")


def init_metrics_routes(app: FastAPI) -> None:
    app.include_router(router)


@router.get("/debug/tracemalloc/{action}", summary="Start tracemalloc")
def tracemalloc_control(action: str, nframe: int = 25):
    if action == "start":
        tracemalloc.start(nframe)
    elif action == "stop":
        tracemalloc.stop()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}",
        )


@router.get("/debug/snapshot", summary="Show top X memory allocations")
def tracemalloc_snapshot(count: int = 20):
    # Check for sensible input
    if count < 1 or count > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count must be between 1 and 100",
        )

    if not tracemalloc.is_tracing():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracemalloc is not started",
        )

    current, peak = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()

    # Ignore <frozen importlib._bootstrap> and <unknown> files
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
            tracemalloc.Filter(False, tracemalloc.__file__),
        )
    )
    top_stats = snapshot.statistics("traceback")
    return {
        "stats": [
            {
                "title": f"{stat.count} memory blocks: {bytes2human(stat.size)}",
                "traces": stat.traceback.format(),
            }
            for stat in top_stats[:count]
        ],
        "current": f"Current memory usage: {current / 1024**2:.4f} MB",
        "peak": f"Peak memory usage: {peak / 1024**2:.4f} MB",
    }


@router.get("/debug/heap/{p:path}")
def heap_usage(p: str):
    gc.collect()

    # grouping the items by
    # - byclodo:    class or dict owner (Default)
    # - bytype:     same as byclodo, but with all the dicts lumped together
    # - byrcs:      reference count stats, i.e. h.referrers.byclodo
    # - byid
    # - byvia:      groupby index, i.e. ".key"
    hpy = h.heap()
    key, stats = "h", ""
    for s in p.split("/"):
        if s.isdigit():
            hpy = hpy[int(s)]
            key = f"{key}[{s}]"
        else:
            hpy = getattr(hpy, s)
            key = f"{key}.{s}"
        stats += f"{key}:\n{str(hpy)}\n\n"
    return Response(content=stats, media_type="text/plain")
