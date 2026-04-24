from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
import models
from models import Base, KnowledgeStatus
import uvicorn
from database import SessionLocal, engine
import crud
from schemas import (
    TaskCreate, TaskSubgroup, TaskGroup, 
    UserCreate, UserLogin, Token, User,
    QuestionProgressUpdate, KnowledgeStatusEnum,
    UserProgressSummary, ProgressSummary, TaskWithProgress
)
import os
from datetime import timedelta
from auth import create_access_token, get_current_user_from_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Question Learning System", version="2.0")

# Получаем директорию текущего файла для правильных путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# OAuth2 схема для авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Зависимость для получения текущего пользователя"""
    user = get_current_user_from_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# === Auth endpoints ===
@app.post("/api/auth/register", response_model=User)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверка существующего пользователя
    existing_user = crud.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    
    existing_email = crud.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    return crud.create_user(db, user_data)

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Вход пользователя и получение токена"""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user

# === Progress endpoints ===
@app.get("/api/progress", response_model=UserProgressSummary)
def get_my_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить прогресс текущего пользователя"""
    summary = crud.get_user_progress_summary(db, current_user.id)
    if not summary:
        raise HTTPException(status_code=404, detail="Прогресс не найден")
    return summary

@app.get("/api/progress/{user_id}", response_model=UserProgressSummary)
def get_user_progress(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить прогресс любого пользователя (для администратора или самого себя)"""
    if current_user.id != user_id:
        # В продакшене здесь можно добавить проверку на админа
        pass
    summary = crud.get_user_progress_summary(db, user_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return summary

@app.get("/api/questions/{question_id}/progress", response_model=dict)
def get_question_progress(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить статус конкретного вопроса для текущего пользователя"""
    progress = crud.get_question_progress(db, current_user.id, question_id)
    if progress:
        return {"question_id": question_id, "status": progress.status.value}
    else:
        return {"question_id": question_id, "status": KnowledgeStatusEnum.DONT_KNOW.value}

@app.put("/api/questions/{question_id}/progress", response_model=dict)
def update_question_progress(
    question_id: int,
    progress_data: QuestionProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить статус вопроса для текущего пользователя"""
    # Проверяем существование вопроса
    task = crud.get_task(db, question_id)
    if not task:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Конвертируем enum из schema в model enum
    status_map = {
        KnowledgeStatusEnum.KNOW: KnowledgeStatus.KNOW,
        KnowledgeStatusEnum.ALMOST_KNOW: KnowledgeStatus.ALMOST_KNOW,
        KnowledgeStatusEnum.DONT_KNOW: KnowledgeStatus.DONT_KNOW
    }
    model_status = status_map[progress_data.status]
    
    progress = crud.update_question_progress(db, current_user.id, question_id, model_status)
    return {"question_id": question_id, "status": progress.status.value, "message": "Прогресс обновлен"}

@app.get("/api/questions/with-progress", response_model=list)
def get_questions_with_progress(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Получить все вопросы со статусом прогресса текущего пользователя"""
    tasks = crud.get_tasks(db)
    user_progress = {p.question_id: p.status for p in crud.get_user_progress(db, current_user.id)}
    
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "question": task.question,
            "answer": task.answer,
            "failed_answer": task.failed_answer,
            "description": task.description,
            "task_subgroup_id": task.task_subgroup_id,
            "task_subgroup": {
                "id": task.task_subgroup.id,
                "name": task.task_subgroup.name,
                "description": task.task_subgroup.description,
                "task_group_id": task.task_subgroup.task_group_id,
                "created_at": task.task_subgroup.created_at.isoformat() if task.task_subgroup.created_at else None
            },
            "user_status": user_progress.get(task.id, KnowledgeStatus.DONT_KNOW).value if task.id in user_progress else KnowledgeStatusEnum.DONT_KNOW.value
        }
        result.append(task_dict)
    
    return result

# === Existing endpoints ===
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """Общедоступная главная страница"""
    # Проверяем, авторизован ли пользователь
    token = request.cookies.get("access_token")
    current_user = None
    progress_summary = None
    
    if not token:
        # Пытаемся получить токен из заголовка (для JS запросов)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if token:
        try:
            current_user = get_current_user_from_token(token, db)
            if current_user:
                progress_summary = crud.get_user_progress_summary(db, current_user.id)
        except Exception:
            current_user = None
    
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
            "current_user": current_user,
            "progress_summary": progress_summary,
        }
    )

@app.get("/guest")
def guest_home(request: Request, db: Session = Depends(get_db)):
    """Страница для неавторизованных пользователей"""
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
        "guest_home.html",
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
    
    # Проверяем авторизацию пользователя
    token = request.cookies.get("access_token")
    current_user = None
    user_progress = {}
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if token:
        try:
            current_user = get_current_user_from_token(token, db)
            if current_user:
                # Получаем прогресс только для авторизованных пользователей
                user_progress = {p.question_id: p.status for p in crud.get_user_progress(db, current_user.id)}
        except Exception:
            current_user = None

    return templates.TemplateResponse("question.html", {
        "request": request,
        "tasks": tasks,
        "subgroups": subgroups,
        "groups": groups,
        "current_user": current_user,
        "user_progress": user_progress,
        "knowledge_statuses": KnowledgeStatusEnum
    })

@app.get("/add-question")
def add_question_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
        "groups": groups_data,
        "current_user": current_user,
    })

@app.post("/api/questions")
def create_question_api(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """API endpoint для создания вопроса"""
    try:
        new_task = crud.create_task(db, task)
        return {"message": "Вопрос успешно добавлен", "task_id": new_task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Страницы входа и регистрации
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "sidebar_sections": {}
    })

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "sidebar_sections": {}
    })


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )