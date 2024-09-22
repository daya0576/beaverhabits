FROM python:3.12-slim AS builder

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get install -y --no-install-recommends \
    build-essential,libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN python -m pip install --upgrade pip
# NiceGUI 1.4.20 - Make libsass optional 
# RUN python -m pip install --upgrade libsass
RUN python -m pip install --upgrade cffi

FROM python:3.12-slim AS release
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

LABEL maintainer="Henry Zhu <daya0576@gmail.com>"

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY start.sh .
COPY beaverhabits ./beaverhabits

CMD ["sh", "start.sh", "prd"]
