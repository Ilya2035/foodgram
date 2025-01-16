# Foodgram

Foodgram — это веб-приложение, в котором пользователи могут делиться кулинарными рецептами,
подписываться на интересных авторов, добавлять рецепты в избранное и формировать список покупок,
чтобы потом скачать его (в формате TXT, PDF или другом удобном виде).

## Оглавление


1. Описание проекта
2. Технологический стек
3. Инструкция по развертыванию (Docker)
4. Как наполнить БД данными
5. Как открыть документацию
6. Примеры запросов и ответов
7. Авторство
8. Сайт и доступ к правам (при необходимости)

## Технологический стек

```
Python 3.8+
Django 3.2
Django REST Framework
PostgreSQL
Gunicorn
Nginx
Docker и docker-compose
```
Из дополнительных библиотек могут использоваться:
```
django-filters, djoser и пр.
```
## Инструкция по развертыванию (Docker)
### Клонируйте репозиторий:

```bash
git clone https://github.com/your-username/foodgram-project.git
```
### Зайдите в дерикторию
```bash
cd foodgram
```
### Создайте файл .env где укажите:
```dotenv
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=False or True
ALLOWED_HOSTS=127.0.0.1,localhost,your_domain
USED_DB=False or True
```
USED_DB при использовании в работе Тrue, в тестировании False, с DEBUG наоборот
### Запустите сборку и контейнеры:

```bash
docker-compose up --build
```
### После успешной сборки и старта контейнеров приложение будет доступно по адресу:
```
http://localhost:9000
```
При внесении изменений отправьте их через Push на Github после чего ваш проект автоматически запуститься 
на сервере который вы можете указать в параметрах в папке .github/workflows через секреты.
так же не забудте поправить файл docker-compose.production.yml

## Как наполнить БД данными
Если база данных пуста (например, после очистки volume или при первом развёртывании), выполните команду для загрузки ингредиентов:

```bash
docker exec -it foodgram-backend-1 python manage.py load_ingredients data/ingredients.json
```
если работатет на локальном сервере, используйте команду без ссылки на контейнер

Также для наполнения базы:

Создайте суперпользователя (если нужно управлять админкой):
```bash
docker exec -it foodgram-backend-1 python manage.py createsuperuser
```
Все команды миграций и т.п. выполняются в аналогичном формате
### Документация

##### Swagger UI: http://localhost:9000/api/docs/
##### Redoc: http://localhost:9000/api/redoc/


## Примеры запросов и ответов
Ниже — несколько примеров того, как можно обращаться к API Foodgram.

Авторизация и получение токена
Запрос:

```bash
POST /api/auth/token/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Qwerty123"
}
```
Пример успешного ответа:

```json
{
  "auth_token": "0123456789abcdef0123456789abcdef01234567"
}
```
Получение списка рецептов
Запрос (без авторизации доступен список, если так задумано):

```bash
GET /api/recipes/
```
Пример успешного ответа:

```json
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "tags": [{ "id": 1, "name": "Завтрак", "slug": "breakfast" }],
      "author": {
        "email": "author@example.com",
        "id": 4,
        "username": "chef_master",
        "first_name": "Виктор",
        "last_name": "Петров",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/avatar.png"
      },
      "ingredients": [
        {
          "id": 1123,
          "name": "Яйцо куриное",
          "measurement_unit": "шт",
          "amount": 4
        }
      ],
      "is_favorited": false,
      "is_in_shopping_cart": false,
      "name": "Яичница",
      "image": "http://foodgram.example.org/media/recipes/image.png",
      "text": "Простая яичница",
      "cooking_time": 5
    }
    ...
  ]
}
```
Добавление рецепта в избранное
Запрос:

```bash
POST /api/recipes/1/favorite/
Authorization: Token 0123456789abcdef0123456789abcdef01234567
```
Пример успешного ответа:

```json
{
  "id": 1,
  "name": "Яичница",
  "image": "http://foodgram.example.org/media/recipes/image.png",
  "cooking_time": 5
}
```
Более подробные примеры запросов и ответов можно смотреть в документации.

### Авторство
Проект разработан https://github.com/Ilya2035

Почта для связи: fyrno2049@gmail.com