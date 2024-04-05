FROM zauberzeug/nicegui:1.4.19

# poetry export -f requirements.txt --without-hashes --output requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .
CMD ["sh", "start.sh", "prod"]
