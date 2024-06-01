FROM python:3.12.2-slim

LABEL maintainer="Henry Zhu <daya0576@gmail.com>"


COPY . .

RUN pip install --upgrade pip \
    && pip install poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev

CMD ["sh", "start.sh", "prd"]
