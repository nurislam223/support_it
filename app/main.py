from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
import models
import uvicorn
from database import SessionLocal, engine
import crud

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=5000,
        reload=True
    )