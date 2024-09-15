FROM python:3.12-slim AS builder

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade libsass

FROM python:3.12-slim AS release
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
ARG VERSION

LABEL maintainer="Henry Zhu <daya0576@gmail.com>"
RUN python -m pip install --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY start.sh .
COPY beaverhabits ./beaverhabits
CMD ["sh", "start.sh", "prd"]
