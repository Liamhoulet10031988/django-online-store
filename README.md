# Интернет-магазин на Django

## Описание

Учебный интернет-магазин, который развивается на протяжении блока Django.
Проект использует PostgreSQL для хранения категорий, товаров и контактных
данных. Управлять записями можно через административную панель Django.

На текущем этапе реализована работа с Django ORM, миграциями, фикстурами и
кастомной командой загрузки тестовых данных.

## Реализовано

- Django-проект с приложением `catalog`;
- главная страница и страница контактов;
- локальное подключение Bootstrap 5;
- PostgreSQL и настройки через переменные окружения;
- модели `Category`, `Product` и `Contact`;
- связь товара с категорией через `ForeignKey`;
- загрузка изображений товаров;
- миграции базы данных;
- административная панель с поиском и фильтрацией;
- фикстура категорий и товаров;
- команда `load_products` для очистки и заполнения базы;
- выборка пяти последних товаров;
- автоматические тесты.

## Структура проекта

```text
config/                         - настройки и главные маршруты Django
catalog/                        - приложение интернет-магазина
catalog/migrations/             - история изменений структуры базы
catalog/fixtures/               - тестовые данные в формате JSON
catalog/management/commands/    - собственные команды manage.py
catalog/templates/catalog/      - HTML-шаблоны приложения
static/                         - CSS и JavaScript Bootstrap
screenshots/                    - скриншоты работы Django shell
manage.py                       - управление Django-проектом
pyproject.toml                  - зависимости и настройки Poetry
.env.example                    - безопасный шаблон переменных окружения
```

## Установка

Установите зависимости:

```bash
poetry install
```

Создайте PostgreSQL-базу `django_online_store`.

Создайте файл `.env` по примеру `.env.example` и укажите свои данные
подключения к PostgreSQL.

## Миграции

```bash
poetry run python manage.py migrate
```

## Тестовые данные

Команда удаляет старые категории и товары, затем загружает фикстуру:

```bash
poetry run python manage.py load_products
```

## Создание администратора

```bash
poetry run python manage.py createsuperuser
```

## Запуск

```bash
poetry run python manage.py runserver
```

После запуска доступны:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/contacts/
http://127.0.0.1:8000/admin/
```

## Тесты и проверки

```bash
poetry run python manage.py check
poetry run python manage.py makemigrations --check
poetry run python manage.py test
poetry run flake8 .
poetry run isort --check-only .
```

Для формирования отчета о покрытии:

```bash
poetry run coverage run manage.py test
poetry run coverage report -m
poetry run coverage html -d coverage_html
```

## Использованные технологии

- Python 3.12;
- Django;
- PostgreSQL;
- Django ORM;
- Poetry;
- HTML5;
- Bootstrap 5;
- Git и GitHub.
