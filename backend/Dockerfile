FROM python:3.10

WORKDIR /app

RUN apt-get update ; apt-get install -y postgresql-client

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:9000", "foodgram.wsgi"]
