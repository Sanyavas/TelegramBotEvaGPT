ARG PYTHON_VERSION=3.10-slim-buster

FROM python:${PYTHON_VERSION}

WORKDIR /app

# Оптимізація кешування шарів
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


# Копіюємо решту файлів
COPY . .

# Запустимо нашу програму всередині контейнера
CMD ["python", "app/main.py"]
