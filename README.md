# Система изучения вопросов с прогрессом пользователей

Production-ready FastAPI приложение для управления вопросами на собеседованиях с системой отслеживания прогресса пользователей.

## Основные возможности

- **Система пользователей**: Регистрация, аутентификация, JWT-токены
- **Управление вопросами**: Группы, подгруппы, вопросы с ответами
- **Отслеживание прогресса**: Статусы "Знаю", "Почти знаю", "Не знаю" для каждого вопроса
- **Визуализация прогресса**: Общий прогресс и по группам вопросов
- **REST API**: Полный набор endpoints для работы с вопросами и прогрессом

## Найденные и исправленные баги

### Критические исправления:

1. **models.py**:
   - Добавлена модель `User` для системы пользователей
   - Добавлена модель `QuestionProgress` для отслеживания прогресса
   - Добавлен enum `KnowledgeStatus` (знаю, почти знаю, не знаю)
   - Обновлены relationships между моделями

2. **schemas.py**:
   - Добавлены схемы для пользователей (UserCreate, UserLogin, Token)
   - Добавлены схемы для прогресса (QuestionProgress, ProgressSummary, UserProgressSummary)
   - Добавлен KnowledgeStatusEnum для API

3. **crud.py**:
   - CRUD операции для пользователей (с хешированием паролей)
   - CRUD операции для прогресса вопросов
   - Функция `get_user_progress_summary()` для получения сводки прогресса по группам

4. **auth.py**:
   - Добавлена функция `get_current_user_from_token()`
   - Убрана обязательная проверка SECRET_KEY для разработки

5. **main.py**:
   - Добавлены endpoints авторизации (/api/auth/register, /api/auth/login, /api/auth/me)
   - Добавлены endpoints прогресса (/api/progress, /api/questions/{id}/progress)
   - Добавлена зависимость `get_current_user` для защиты routes
   - Обновлены существующие endpoints для работы с авторизацией

6. **templates/**:
   - Создан `login.html` - страница входа
   - Создан `register.html` - страница регистрации
   - Обновлен `base.html` - добавлена авторизация и стили
   - Обновлен `question.html` - добавлено отображение прогресса и кнопки управления

7. **docker-compose.yml**:
   - Обновлены переменные окружения
   - Добавлены volumes для templates/static

8. **.env.example**:
   - Обновлен DATABASE_URL

## Запуск приложения

### Через Docker Compose (рекомендуется):

```bash
cd app

# Копирование .env.example в .env и настройка переменных
cp .env.example .env

# Редактирование .env (особенно SECRET_KEY!)
nano .env

# Запуск
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

Приложение будет доступно по адресу: http://localhost:8080

### Локально:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Копирование и настройка .env
cp .env.example .env

# Запуск
cd app
python main.py
```

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| DATABASE_URL | URL подключения к БД | postgresql://admin:admin@localhost:5432/questions_db |
| SECRET_KEY | Секретный ключ для JWT (мин. 32 символа) | super-secret-key-min-32-chars |
| ACCESS_TOKEN_EXPIRE_MINUTES | Время жизни токена в минутах | 30 |
| DEBUG | Режим отладки | false |

## API Endpoints

### Авторизация
- `POST /api/auth/register` - Регистрация нового пользователя
- `POST /api/auth/login` - Вход и получение токена
- `GET /api/auth/me` - Информация о текущем пользователе

### Прогресс
- `GET /api/progress` - Прогресс текущего пользователя
- `GET /api/progress/{user_id}` - Прогресс любого пользователя
- `GET /api/questions/{question_id}/progress` - Статус конкретного вопроса
- `PUT /api/questions/{question_id}/progress` - Обновление статуса вопроса
- `GET /api/questions/with-progress` - Все вопросы со статусами

### Вопросы
- `GET /questions` - Страница всех вопросов
- `POST /api/questions` - Создание нового вопроса
- `GET /add-question` - Страница добавления вопроса

## Структура прогресса

Каждый пользователь может отметить свой прогресс по каждому вопросу:

- **Знаю** (green) - уверенно знаю ответ
- **Почти знаю** (yellow) - нужно повторить
- **Не знаю** (red) - не знаком с темой

Прогресс отображается:
- В виде бейджей рядом с каждым вопросом
- В общей статистике с процентом изученного
- В разбивке по группам вопросов

## Технологии

- **Backend**: FastAPI, SQLAlchemy, Pydantic v2
- **Auth**: JWT (python-jose), bcrypt (passlib)
- **Database**: PostgreSQL (через psycopg2-binary)
- **Frontend**: Jinja2 templates, Bootstrap 5, vanilla JS
- **Deployment**: Docker, Docker Compose
