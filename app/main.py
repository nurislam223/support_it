from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

# (опционально) если будут статические файлы (css, js, img)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home(request: Request):
    sidebar_sections = [
        {"title": "Общие вопросы", "items": ["Рассказ о себе", "Достоинства", "Регулярные задачи"]},
        {"title": "Неудобные вопросы", "items": ["Военный билет", "Причина смены места работы"]},
        {"title": "API", "items": ["Определение API", "Определение REST API"]},
        {"title": "SQL", "items": ["Определение SQL", "Операторы SQL"]},
        {"title": "Логи и мониторинг", "items": ["Инструменты логов и мониторинга"]},
    ]

    softs = [
        {"title": "Общие вопросы", "description": "Graphic design is the process of visual communication and problem-solving", "image": "/static/images/Image_4.jpg"},
        {"title": "Неудобные вопросы", "description": "Information architecture is the art and science of structuring and organizing information", "image": "/static/images/Image_5.jpg"},
        {"title": "Работа в поддержке", "description": "It is a form of solution-based thinking with the intent of producing a constructive future result", "image": "/static/images/Image_6.jpg"},
    ]

    hards = [{"title": "API",
              "description": "Graphic design is the process of visual communication and problem-solving",
              "image": "/static/images/Image_1.jpg", "progress": "20%"},
        {"title": "SQL",
         "description": "Information architecture is the art and science of structuring and organizing information",
         "image": "/static/images/Image_2.jpg"},
        {"title": "Логи и мониторинг",
         "description": "It is a form of solution-based thinking with the intent of producing a constructive future result",
         "image": "/static/images/Image_3.jpg"},
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
