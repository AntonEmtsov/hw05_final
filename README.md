[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)

# Соцсеть Yatube
Социальная сеть блогеров.

Технологии:
```
Python 3.8
Django 2.2.19
```

## Инструкции по установке
Клонируйте репозиторий:
```
git clone https://github.com/russ044/hw05_final.git
```

Установите и активируйте виртуальное окружение:
```
python -m venv venv
.\venv\Scripts\activate
```

Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

Примените миграции:
```
python manage.py migrate
```

Запуск:
```
python manage.py runserver
```
