FROM python:3.9

RUN apt-get update && apt-get install -y postgresql-server-dev-all gcc python3-dev musl-dev

RUN apt-get -y upgrade

RUN pip install --upgrade pip

RUN pip install psycopg2-binary
RUN pip install pyotp
RUN pip install --no-cache-dir apscheduler


COPY . /thread

VOLUME ["/thread"]

WORKDIR /thread

RUN mkdir -p logs

EXPOSE 7000

CMD ["python", "thread.py"]