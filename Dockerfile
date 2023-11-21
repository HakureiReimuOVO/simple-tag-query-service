FROM python:3.7-slim

LABEL authors="hakurei"

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "server.py"]