"""
OpenTelemetry integration for BeaverHabits.

Only active when opentelemetry-sdk and exporter packages are installed
(i.e. the `fly` dependency group). Everywhere else this module is a no-op,
so the rest of the codebase never needs to guard against ImportError itself.

Usage
-----
    from beaverhabits.telemetry import traced

    @traced
    async def my_func():
        ...

    # Custom span name:
    @traced("my_service.my_func")
    async def my_func():
        ...
"""

from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING, Callable, TypeVar

from beaverhabits.logger import logger

if TYPE_CHECKING:
    from fastapi import FastAPI

F = TypeVar("F", bound=Callable)


# ---------------------------------------------------------------------------
# No-op fallback – used when OTel packages are not installed
# ---------------------------------------------------------------------------

class _NoOpSpan:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def set_attribute(self, *_):
        pass


class _NoOpTracer:
    def start_as_current_span(self, name: str, **kwargs):
        return _NoOpSpan()


def _noop_instrument_app(_app: "FastAPI") -> None:
    pass


# ---------------------------------------------------------------------------
# Real OTel implementation (only imported when packages are available)
# ---------------------------------------------------------------------------

def _build_real_setup():
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        def setup_telemetry(app: "FastAPI", endpoint: str, service_name: str) -> None:
            resource = Resource(attributes={SERVICE_NAME: service_name})
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider = TracerProvider(resource=resource)
            # SimpleSpanProcessor: export immediately (good for dev/debugging).
            # Switch to BatchSpanProcessor in high-traffic production if needed.
            provider.add_span_processor(SimpleSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            logger.info(f"OpenTelemetry tracer provider set up → {endpoint}")

            # Auto-instrument FastAPI (HTTP spans)
            # NiceGUI registers ALL page routes on its own `nicegui.app` instance,
            # NOT on the main FastAPI app. We need to instrument both.
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor.instrument_app(app)
                logger.info("OTel: main FastAPI app instrumented")
            except Exception as e:
                logger.warning(f"OTel: FastAPI instrumentation failed: {e}")

            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                from nicegui import app as nicegui_app
                FastAPIInstrumentor.instrument_app(nicegui_app)
                logger.info("OTel: NiceGUI app instrumented")
            except ImportError:
                pass  # NiceGUI not in this environment
            except Exception as e:
                logger.warning(f"OTel: NiceGUI instrumentation failed: {e}")

            # Auto-instrument SQLAlchemy (SQL spans)
            try:
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
                from beaverhabits.app.db import engine
                SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
                logger.info("OTel: SQLAlchemy instrumented")
            except Exception as e:
                logger.warning(f"OTel: SQLAlchemy instrumentation failed: {e}")

            # Auto-instrument httpx (outbound HTTP – backups, Paddle, etc.)
            try:
                from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
                HTTPXClientInstrumentor().instrument()
                logger.info("OTel: HTTPX instrumented")
            except Exception as e:
                logger.warning(f"OTel: HTTPX instrumentation failed: {e}")

        def get_tracer(name: str):
            return trace.get_tracer(name)

        return setup_telemetry, get_tracer

    except ImportError:
        return None, None


_real_setup, _real_get_tracer = _build_real_setup()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_telemetry(app: "FastAPI") -> None:
    """Call once at application startup (after the FastAPI app is created)."""
    try:
        from beaverhabits.configs import settings
        endpoint = settings.OTEL_ENDPOINT
        service_name = settings.OTEL_SERVICE_NAME

        if not endpoint:
            logger.debug("OTel: OTEL_ENDPOINT not set, tracing disabled")
            return

        if _real_setup is None:
            logger.warning("OTel: packages not installed, tracing disabled")
            return

        _real_setup(app, endpoint, service_name)
    except Exception as e:
        logger.warning(f"OTel: init_telemetry failed, continuing without tracing: {e}")


def get_tracer(name: str):
    """
    Return an OpenTelemetry Tracer, or a no-op tracer if OTel is unavailable.
    Safe to call at module import time.
    """
    try:
        if _real_get_tracer is not None:
            return _real_get_tracer(name)
    except Exception:
        pass
    return _NoOpTracer()


def carry_trace_context(fn: F) -> F:
    """
    Capture the current OTel context and re-attach it when fn is called later
    in a different asyncio Task (e.g. NiceGUI on_connect callbacks).

    Usage – inside a page handler where the HTTP span is active:
        client.on_connect(carry_trace_context(my_callback))
    """
    try:
        if _real_get_tracer is None:
            return fn
        from opentelemetry import context as otel_context
        ctx = otel_context.get_current()

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            token = otel_context.attach(ctx)
            try:
                return await fn(*args, **kwargs)
            finally:
                otel_context.detach(token)
        return wrapper  # type: ignore[return-value]
    except Exception:
        return fn


def traced(_func: F | str | None = None, *, name: str | None = None) -> F:
    """
    Decorator that wraps a function (sync or async) in an OTel span.

    Usage::

        @traced
        async def my_func(): ...

        @traced("custom.span.name")
        async def my_func(): ...
    """
    # Support @traced("name") — string passed as first positional arg
    if isinstance(_func, str):
        name = _func
        _func = None
    def decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__qualname__}"
        tracer = get_tracer(func.__module__)

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name):
                    return await func(*args, **kwargs)
            return async_wrapper  # type: ignore[return-value]
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with tracer.start_as_current_span(span_name):
                    return func(*args, **kwargs)
            return sync_wrapper  # type: ignore[return-value]

    # Support both @traced and @traced("name")
    if _func is not None:
        return decorator(_func)
    return decorator  # type: ignore[return-value]
