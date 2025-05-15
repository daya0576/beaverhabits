import gc
import tracemalloc

import psutil
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter()


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"
    stats: dict = {}


@router.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def read_root():
    return HealthCheck(status="OK")


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
def tracemalloc_control(action: str):
    if action == "start":
        tracemalloc.start()
    elif action == "stop":
        tracemalloc.stop()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}",
        )


@router.get("/debug/snapshot", summary="Show top X memory allocations")
def tracemalloc_snapshot(count: int = 10):
    current, peak = tracemalloc.get_traced_memory()

    # Check for sensible input
    if count < 1 or count > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count must be between 1 and 100",
        )

    snapshot = tracemalloc.take_snapshot()

    # Ignore <frozen importlib._bootstrap> and <unknown> files
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        )
    )
    top_stats = snapshot.statistics("lineno")
    return {
        "stats": [str(stat) for stat in top_stats[:count]],
        "current": f"Current memory usage: {current / 1024**2:.4f} MB",
        "peak": f"Peak memory usage: {peak / 1024**2:.4f} MB",
    }
