# Kittygram: паспорт здоровья кота

Проект расширяет [оригинальный Kittygram](https://github.com/yandex-praktikum/kittygram) (коммит `286ea93a4319a70a4845244494e5bbd1f91773c0`). Для каждого кота владелец может хранить визиты и процедуры, связывать их с клиникой и отмечать выполнение. Клинику добавляет администратор. Существующие записи котов без владельца остаются в базе после миграции, но паспорт для них недоступен до назначения владельца администратором.

## Запуск

Исходные зависимости зафиксированы в `requirements.txt` (Django 3.2, DRF 3.12.4). Используйте Python 3.9.

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Задайте в `.env` собственный `DJANGO_SECRET_KEY`, например с помощью `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`. Пустое значение включает случайный ключ на время запуска. `DJANGO_DEBUG=true` предназначен для локальной разработки. Затем:

```bash
set -a; source .env; set +a
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Для API используется Basic Auth штатного DRF. В Postman задайте `username` и `password` обычного пользователя и `admin_username` и `admin_password` сотрудника в переменных коллекции [Kittygram-health.postman_collection.json](Kittygram-health.postman_collection.json). Запросы идут в порядке создания клиники, кота и записи; ID из ответов сохраняются в переменные коллекции. Запрос `POST /cats/` назначает текущего пользователя владельцем; `GET /cats/` сохраняет исходный публичный список.

## Данные и права

`Clinic`: уникальное название, адрес, необязательный телефон. `HealthRecord`: кот, необязательная клиника, тип `visit` или `procedure`, дата, статус `planned` или `completed`, описание. Завершённая запись не может быть датирована будущим; повторное завершение и возврат завершённой записи в план запрещены. При удалении кота его записи удаляются; при удалении клиники ссылка в записи очищается.

Паспорт читается и меняется только владельцем кота. Запрос чужого кота или записи возвращает 404. Неавторизованный запрос к паспорту или справочнику клиник отклоняется. Авторизованный пользователь читает клиники, сотрудник (`is_staff`) может добавить клинику.

## API

| Метод | Путь | Роль | Успех |
|---|---|---|---|
| GET | `/api/cats/{cat_id}/health-records/` | владелец | 200 |
| POST | `/api/cats/{cat_id}/health-records/` | владелец | 201 |
| GET | `/api/health-records/{id}/` | владелец | 200 |
| PATCH | `/api/health-records/{id}/` | владелец | 200 |
| DELETE | `/api/health-records/{id}/` | владелец | 204 |
| POST | `/api/health-records/{id}/complete/` | владелец | 200 |
| GET | `/api/clinics/` | авторизованный | 200 |
| POST | `/api/clinics/` | администратор | 201 |

Для списка доступны `type=visit|procedure`, `date_from=YYYY-MM-DD`, `date_to=YYYY-MM-DD`, `page`, `page_size` (по умолчанию 10, максимум 100). Ответ списка имеет поля `count`, `next`, `previous`, `results`. Ошибки некорректных фильтров и валидации возвращают 400; попытка обычного пользователя создать клинику возвращает 403.

Пример запроса:

```http
POST /api/cats/1/health-records/
Content-Type: application/json

{"record_type":"visit","date":"2026-01-01","clinic":1,"description":"Плановый осмотр"}
```

Форма успешного ответа:

```json
{"id":1,"cat":1,"clinic":1,"record_type":"visit","date":"2026-01-01","status":"planned","description":"Плановый осмотр"}
```

Форма ошибки повторного завершения:

```json
{"status":["Запись уже завершена."]}
```

Проверка: `python manage.py test health`. Значения идентификаторов в примерах зависят от базы.
