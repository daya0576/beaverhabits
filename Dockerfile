FROM python:3.12.2-slim

LABEL maintainer="Henry Zhu <daya0576@gmail.com>"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .
CMD ["sh", "start.sh", "prd"]
