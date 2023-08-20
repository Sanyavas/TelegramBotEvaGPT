ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

WORKDIR .

COPY . .

RUN pip install -r requirements.txt


# Запустимо нашу програму всередині контейнера
CMD ["python", "app/main.py"]
