# Foodgram Project

## Оглавление
- [Зависимости](#зависимости)  
- [Описание проекта](#описание-проекта)
- [Запуск проекта](#запуск-проекта)

## Зависимости<a name="зависимости"></a>
🐍Python 3.9, 🖥️ Django 3.2.3, 🔄 Django Rest Framework 3.12.4,  
🖌️ Nginx 1.22.1, 📚 Postgres 13.0, ☁️ YandexCloud (server)


## Описание проекта <a name="описание-проекта"></a> 
Приложение «Продуктовый помощник» - сайт, на котором пользователи могут публиковать рецепты и подписываться на публикации понравившихся авторов. Также, сервис позволит добавить понравившийся рецепт в избранное, а после создать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Запуск проекта <a name="запуск-проекта"></a>
### Заполнение `.env`-файла
Для начала необходимо перейти в директорию `infra/`. В директории создайте файл `.env` со следующими переменными:  

- DEBUG
- TEST_DATABASE=Tru
- DB_NAME
- POSTGRES_USER
- POSTGRES_PASSWORD
- DB_HOST
- DB_PORT
- ALLOWED_HOSTS
- SECRET_KEY

###### Пример заполнения .env-файла можно найти в файле `infra/env.example`

### Запуск локально

Клонировать репозиторий
```
git clone git@github.com:MrPierreDunn/foodgram-project-react.git
```
Cоздать и активировать виртуальное окружение:
```
python -m venv venv
source venv/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Перейти в директорию `infra/`
```
cd infra/
```
Создать `.env`-файл
```
nano .env
```
Запустить `docker-compose.yml`
```
docker-compose up
```
Выполнить миграции, сборку статических файлов, заполнить базу данных ингредиентами, создать суперпользователя
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py csv_upload
docker-compose exec backend python manage.py createsuperuser
```
