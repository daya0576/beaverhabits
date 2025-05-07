FROM python:3.13-slim AS python-base
ENV UV_COMPILE_BYTECODE=1 \
    \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"
ENV PATH="$VENV_PATH/bin:$PATH"


FROM python-base AS builder-base
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
WORKDIR $PYSETUP_PATH
ADD https://astral.sh/uv/0.5.26/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-install-project --no-dev -v

# [Experimental] Remove unused nicegui libs
ENV NICEGUI_LIB_PATH="$VENV_PATH/lib/python*/site-packages/nicegui/elements/lib"
RUN for path in $(ls -d $NICEGUI_LIB_PATH); do \
    rm -rf "$path/mermaid/" && \
    rm -rf "$path/plotly/" && \
    rm -rf "$path/vanilla-jsoneditor/"; \
done

FROM python-base AS production
EXPOSE 8080
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
WORKDIR /app
COPY start.sh .
COPY beaverhabits ./beaverhabits
COPY statics ./statics
COPY healthcheck.py .
RUN chmod -R g+w /app && \
    chown -R nobody /app
USER nobody

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python healthcheck.py

CMD ["sh", "start.sh", "prd"]
