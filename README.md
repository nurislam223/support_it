# FastAPI Task Manager - Production Ready

## Найденные и исправленные баги

### Критические исправления:

1. **models.py**:
   - Удалена ошибочная импортированная строка `from sentry_sdk.tracing import SENTRY_TRACE_HEADER_NAME`
   - Заменен устаревший `sqlalchemy.ext.declarative.declarative_base` на `sqlalchemy.orm.declarative_base`

2. **database.py**:
   - Удалена неиспользуемая импорта `DatabaseConfig, Config`
   - Добавлен импорт `declarative_base` для экспорта

3. **main.py**:
   - Исправлены абсолютные пути к шаблонам и статическим файлам через `BASE_DIR`
   - Добавлено создание таблиц БД при запуске: `Base.metadata.create_all(bind=engine)`
   - Изменен хост с `localhost` на `0.0.0.0` для Docker-контейнера
   - Отключен `reload=True` для продакшена
   - Добавлен `log_level="info"`

4. **crud.py**:
   - Заменен устаревший метод `.dict()` на `.model_dump()` для Pydantic v2

5. **auth.py**:
   - Добавлена обязательная проверка наличия `SECRET_KEY` через переменную окружения
   - Убрано значение по умолчанию для секретного ключа

6. **requirements.txt**:
   - Удалены ненужные зависимости (pip, attrs, distro, protobuf, pillow, filelock)
   - Добавлены необходимые зависимости: sqlalchemy, uvicorn, python-jose, passlib, python-multipart, environs, psycopg2-binary

7. **Dockerfile**:
   - Добавлена установка `libpq-dev` для psycopg2
   - Удален флаг `--reload` для продакшена

8. **docker-compose.yml**:
   - Удалены volume-монтирования исходного кода (не нужно в проде)
   - Добавлен сервис PostgreSQL с постоянным хранилищем
   - Настроены переменные окружения через env-файл
   - Добавлены `depends_on` и `restart: unless-stopped`
   - Удалена development watch-конфигурация

### Дополнительные улучшения:

- Создан `.env.example` с примером конфигурации
- Создан `.gitignore` для игнорирования временных файлов
- Все конфиги адаптированы для production-использования

## Запуск приложения

### Локально:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Копирование .env.example в .env и настройка переменных
cp .env.example .env

# Запуск
cd app
python main.py
```

### Через Docker Compose:

```bash
cd app

# Копирование .env.example в .env и настройка переменных
cp .env.example .env

# Запуск
docker-compose up --build -d
```

Приложение будет доступно по адресу: http://localhost:8080

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| DATABASE_URL | URL подключения к БД | postgresql://user:pass@host:5432/dbname |
| SECRET_KEY | Секретный ключ для JWT (мин. 32 символа) | super-secret-key-min-32-chars |
| ACCESS_TOKEN_EXPIRE_MINUTES | Время жизни токена в минутах | 30 |
| DEBUG | Режим отладки | False |
