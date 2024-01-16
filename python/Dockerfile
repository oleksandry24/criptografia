FROM python:3.9

RUN apt-get update && apt-get install -y postgresql-server-dev-all gcc python3-dev musl-dev

RUN apt-get install -y git

RUN pip install --upgrade pip

RUN pip install flask==3.0.0

RUN pip install psycopg2-binary
RUN pip install pyotp
RUN pip install --no-cache-dir apscheduler
RUN pip install --no-cache-dir numpy
RUN pip install torch==1.10.0+cpu torchvision==0.11.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html
RUN pip install tqdm tiktoken
RUN pip install openai-whisper --no-deps

RUN pip install numba

RUN apt-get install -y ffmpeg
RUN apt-get install -y gcc  

COPY . /app

VOLUME ["/app"]

WORKDIR /app

RUN mkdir -p logs

EXPOSE 5000

CMD ["python", "app.py"]