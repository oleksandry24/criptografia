FROM python:3.9-alpine3.18


RUN apk update && \
        apk add postgresql-dev gcc python3-dev musl-dev


RUN pip install --upgrade pip

RUN pip install flask==3.0.0

RUN pip install psycopg2-binary
RUN pip install pyotp
RUN pip install --no-cache-dir apscheduler
RUN apk add --no-cache git
RUN pip install openai-whisper --no-deps
RUN pip install --no-cache-dir numpy
RUN pip install torch==1.10.0+cpu torchvision==0.11.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

RUN apk add --no-cache ffmpeg

RUN apk add --no-cache libgomp
COPY . /app

VOLUME ["/app"]

WORKDIR /app

RUN mkdir -p logs

EXPOSE 5000

CMD ["python", "app.py"]