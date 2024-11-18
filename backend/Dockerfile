# backend/Dockerfile

# Используем официальный Python образ в качестве базового
FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /app

RUN apt-get update ; apt-get install -y postgresql-client

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Команда для запуска приложения
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]