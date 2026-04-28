from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
import models
import uvicorn
from database import SessionLocal, engine
import crud
from schemas import TaskCreate, TaskUpdate, TaskGroupCreate, TaskSubgroupCreate

app = FastAPI()

# Убедитесь, что пути правильные
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

@app.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    """Страница администратора для добавления вопросов"""
    tasks = crud.get_tasks(db)
    subgroups = crud.get_task_subgroups(db)
    groups = crud.get_task_groups(db)

    # Формируем sidebar_sections для бокового меню
    sidebar_sections = {}
    for group in groups:
        sidebar_sections[group.name] = [subgroup.name for subgroup in group.task_subgroups]

    # Преобразуем модели SQLAlchemy в словари для JSON сериализации
    subgroups_data = [
        {
            "id": sg.id,
            "name": sg.name,
            "description": sg.description,
            "task_group_id": sg.task_group_id
        }
        for sg in subgroups
    ]

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "tasks": tasks,
        "subgroups": subgroups_data,
        "groups": groups,
        "sidebar_sections": sidebar_sections
    })

# API endpoints для задач (вопросов)
@app.get("/api/tasks/")
def api_get_tasks(db: Session = Depends(get_db)):
    """Получить все задачи"""
    return crud.get_tasks(db)

@app.get("/api/tasks/{task_id}")
def api_get_task(task_id: int, db: Session = Depends(get_db)):
    """Получить задачу по ID"""
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

@app.post("/api/tasks/")
def api_create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Создать новую задачу"""
    return crud.create_task(db, task)

@app.put("/api/tasks/{task_id}")
def api_update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Обновить задачу"""
    task = crud.update_task(db, task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

@app.delete("/api/tasks/{task_id}")
def api_delete_task(task_id: int, db: Session = Depends(get_db)):
    """Удалить задачу"""
    success = crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"message": "Задача успешно удалена"}

# API endpoints для групп задач
@app.get("/api/task-groups/")
def api_get_task_groups(db: Session = Depends(get_db)):
    """Получить все группы задач"""
    return crud.get_task_groups(db)

@app.post("/api/task-groups/")
def api_create_task_group(group: TaskGroupCreate, db: Session = Depends(get_db)):
    """Создать новую группу задач"""
    return crud.create_task_group(db, group)

# API endpoints для подгрупп задач
@app.get("/api/task-subgroups/")
def api_get_task_subgroups(db: Session = Depends(get_db)):
    """Получить все подгруппы задач"""
    return crud.get_task_subgroups(db)

@app.post("/api/task-subgroups/")
def api_create_task_subgroup(subgroup: TaskSubgroupCreate, db: Session = Depends(get_db)):
    """Создать новую подгруппу задач"""
    return crud.create_task_subgroup(db, subgroup)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=5000,
        reload=True
    )