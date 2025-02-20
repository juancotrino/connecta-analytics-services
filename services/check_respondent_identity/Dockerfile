FROM python:3.11.1-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git

COPY . .

RUN pip install -r requirements.txt

ENV PORT=8080

EXPOSE ${PORT}

ENTRYPOINT ["python", "main.py"]
