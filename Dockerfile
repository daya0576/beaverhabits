FROM python:3.12-slim

LABEL maintainer="Henry Zhu <daya0576@gmail.com>"

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev python3-pip libxml2-dev libxslt1-dev zlib1g-dev g++ \
    && pip install -r requirements.txt \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove gcc python3-dev python3-pip libxml2-dev libxslt1-dev zlib1g-dev g++



COPY . .
CMD ["sh", "start.sh", "prd"]
