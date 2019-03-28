FROM python:3.6-alpine

RUN apk update
RUN apk add gcc
RUN apk add musl-dev

WORKDIR /fibsrv
COPY ./backend /fibsrv
COPY ./requirements.txt /fibsrv

RUN python3 -m pip install -r requirements.txt
CMD ["python3", "main.py"]

EXPOSE 5000
