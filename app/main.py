from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

# (опционально) если будут статические файлы (css, js, img)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home(request: Request):
    sidebar_sections = [
        {"title": "Общие вопросы", "items": ["Рассказ о себе", "Достоинства", "Регулярные задачи"]},
        {"title": "Неудобные вопросы", "items": ["Военный билет", "Причина смены места работы"]},
        {"title": "API", "items": ["Определение API", "Определение REST API"]},
        {"title": "SQL", "items": ["Определение SQL", "Операторы SQL"]},
        {"title": "Логи и мониторинг", "items": ["Инструменты логов и<br>мониторинга"]},
    ]

    softs = [
        {"title": "Общие вопросы", "description": "Graphic design is the process of visual communication and problem-solving", "image": "https://placehold.co/360x300"},
        {"title": "Неудобные вопросы", "description": "Information architecture is the art and science of structuring and organizing information", "image": "https://placehold.co/360x300"},
        {"title": "Работа в поддержке", "description": "It is a form of solution-based thinking with the intent of producing a constructive future result", "image": "https://placehold.co/360x300"},
    ]

    hards = [{"title": "API",
              "description": "Graphic design is the process of visual communication and problem-solving",
              "image": "https://placehold.co/360x300", "progress": "20%"},
        {"title": "SQL",
         "description": "Information architecture is the art and science of structuring and organizing information",
         "image": "https://placehold.co/360x300"},
        {"title": "Логи и мониторинг",
         "description": "It is a form of solution-based thinking with the intent of producing a constructive future result",
         "image": "https://placehold.co/360x300"},
    ]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sidebar_sections": sidebar_sections,
            "softs": softs,
            "hards": hards,
        }
    )
