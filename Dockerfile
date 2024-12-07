FROM python:3.12-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################
FROM python-base AS builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        curl

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python3 -
# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./
# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --only main

# [Experimental] Remove unused nicegui libs
ENV NICEGUI_LIB_PATH="/opt/pysetup/.venv/lib/python3.12/site-packages/nicegui/elements/lib"
RUN rm -rf "$NICEGUI_LIB_PATH/mermaid/"
RUN rm -rf "$NICEGUI_LIB_PATH/plotly/"
RUN rm -rf "$NICEGUI_LIB_PATH/vanilla-jsoneditor/"


################################
# PRODUCTION
# Final image used for runtime
################################
FROM python-base AS production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

WORKDIR /app
COPY start.sh .
COPY beaverhabits ./beaverhabits
COPY statics ./statics

RUN chmod -R g+w /app && \
    chown -R nobody /app
USER nobody

CMD ["sh", "start.sh", "prd"]
