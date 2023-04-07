FROM python:3.8 as builder
WORKDIR /bot
RUN apt update -y && \
    apt upgrade -y
COPY Pipfile Pipfile.lock /bot/
RUN pip install pipenv && \
    pipenv install --system

FROM python:3.8-slim
WORKDIR /bot
RUN apt update -y && \
    apt upgrade -y && \
    apt-get install libgl1-mesa-dev -y \
    apt-get install libglib2.0-0 -y

ENV PYTHONBUFFERED=1
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages

COPY . /bot
