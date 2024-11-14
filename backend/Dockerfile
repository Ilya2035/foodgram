# backend/Dockerfile

# Используем официальный Python образ в качестве базового
FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Выполняем миграции и собираем статические файлы
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Открываем порт
EXPOSE 8000

# Команда для запуска приложения
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]