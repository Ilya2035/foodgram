# Инструкция по тестированию и запуску проекта

## Локальный запуск

1. Убедитесь, что в настройках проекта `DEBUG` установлен в `True`.

2. Из директории backend выполните команду:
   ```bash
   python manage.py load_ingredients data/ingredients.json
   ```
Это загрузит ингредиенты в базу данных.

3. Запустите проект:
    ```bash
    docker-compose up --build
   ```
После этого проект будет доступен по адресу http://localhost:9000.

## Запуск на сервере

Внесите необходимые изменения в проект или
повторно воспользуйтесь GitHub Actions (если у вас что-то не так).

Если на сервере пропали ингредиенты или вы чистили базу данных, или volume, 
используйте команду:

   ```bash
   docker exec -it foodgram-backend-1 python manage.py load_ingredients data/ingredients.json
   ```

## Сайт и доступ к правам

   ```bash
   http://fyrno.ru
   ```

Manager

Manager@mail.ru

Uhtxrf12
