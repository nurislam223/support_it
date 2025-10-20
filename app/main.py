# main.py
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import SessionLocal, engine
import models
from sqlalchemy.orm import Session, joinedload
import uvicorn


app = FastAPI()

# Подключаем шаблоны и статику
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    # Получаем все группы с подгруппами для сайдбара
    groups = db.query(models.TaskGroups)\
               .options(joinedload(models.TaskGroups.task_subgroups))\
               .all()

    sidebar_sections = {}
    for group in groups:
        sidebar_sections[group.name] = [subgroup.name for subgroup in group.task_subgroups]

    # Получаем группы для "Софтов" и "Хардов" по ID
    softs = db.query(models.TaskGroups)\
              .filter(models.TaskGroups.id.in_([1, 2]))\
              .all()

    hards = db.query(models.TaskGroups)\
              .filter(models.TaskGroups.id.in_([6, 7, 8]))\
              .all()

    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "sidebar_sections": sidebar_sections,
            "softs": softs,
            "hards": hards,
        }
    )

# @app.get("/{task_groups}/{task}")
# def get_task_groups(task_groups: int, task: int):
#     task =




if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",  # доступ с любого IP
        port=5000,       # порт
        reload=True      # автоматическая перезагрузка при изменениях
    )