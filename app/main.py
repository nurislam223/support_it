from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from app import models
import uvicorn
from app.database import SessionLocal, engine
from app import crud
from app.schemas import TaskCreate, TaskSubgroup, TaskGroup

app = FastAPI()

# Убедитесь, что пути правильные
templates = Jinja2Templates(directory="templates")
app.mount("static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    groups = db.query(models.TaskGroups) \
        .options(joinedload(models.TaskGroups.task_subgroups)) \
        .all()

    sidebar_sections = {}
    for group in groups:
        sidebar_sections[group.name] = [subgroup.name for subgroup in group.task_subgroups]

    softs = db.query(models.TaskGroups) \
        .filter(models.TaskGroups.id.in_([1, 2])) \
        .all()

    hards = db.query(models.TaskGroups) \
        .filter(models.TaskGroups.id.in_([6, 7, 8])) \
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

@app.get("/questions")
def get_questions_page(request: Request, db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db)
    subgroups = crud.get_task_subgroups(db)
    groups = crud.get_task_groups(db)

    return templates.TemplateResponse("question.html", {
        "request": request,
        "tasks": tasks,
        "subgroups": subgroups,
        "groups": groups
    })

@app.get("/add-question")
def add_question_page(request: Request, db: Session = Depends(get_db)):
    """Страница для добавления нового вопроса"""
    subgroups = crud.get_task_subgroups(db)
    groups = crud.get_task_groups(db)

    # Конвертируем в словари для JSON сериализации
    subgroups_data = [
        {"id": sg.id, "name": sg.name, "task_group_id": sg.task_group_id}
        for sg in subgroups
    ]
    groups_data = [
        {"id": g.id, "name": g.name, "description": g.description}
        for g in groups
    ]

    return templates.TemplateResponse("add_question.html", {
        "request": request,
        "subgroups": subgroups_data,
        "groups": groups_data
    })

@app.post("/api/questions")
def create_question_api(task: TaskCreate, db: Session = Depends(get_db)):
    """API endpoint для создания вопроса"""
    try:
        new_task = crud.create_task(db, task)
        return {"message": "Вопрос успешно добавлен", "task_id": new_task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8080,
        reload=True
    )