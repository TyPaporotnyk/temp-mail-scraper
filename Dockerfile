FROM python:3.14-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ="UTC"
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt -y install -qq gcc curl libffi-dev xvfb libgtk-3-0 libx11-xcb1 libasound2 && \
    apt -y clean

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi --without=dev

COPY . /app
COPY ./entrypoint.sh /entrypoint.sh

RUN camoufox fetch

RUN chmod +x /entrypoint.sh

WORKDIR /app
