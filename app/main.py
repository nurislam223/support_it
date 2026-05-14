from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from app import models
import uvicorn
from app.database import SessionLocal, engine
from app import crud
from app.schemas import TaskCreate, TaskSubgroup, TaskGroup, UserCreate, QuestionProgressCreate, GroupAnalytics
from app.auth import create_access_token, verify_token, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import os

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

@app.middleware("http")
async def https_scheme_middleware(request: Request, call_next):
    if "x-forwarded-proto" in request.headers:
        request.scope["scheme"] = request.headers["x-forwarded-proto"]
    response = await call_next(request)
    return response

# Use absolute paths relative to this file's location
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Получение текущего пользователя из cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = verify_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    user = crud.get_user_by_username(db, username=username)
    return user

def require_admin(user: models.User = Depends(get_current_user_from_cookie)):
    """Требует чтобы пользователь был админом"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется права администратора"
        )
    return user

@app.get("/")
def home(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    groups = db.query(models.TaskGroups).all()
    
    # Получаем все группы с количеством вопросов в каждой
    all_groups_with_counts = []
    for group in groups:
        questions_count = len(crud.get_tasks_by_group(db, group.id))
        all_groups_with_counts.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "image": group.image,
            "questions_count": questions_count
        })

    is_admin = user.is_admin if user else False

    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "groups": groups,
            "all_groups": all_groups_with_counts,
            "is_admin": is_admin,
            "current_user": user,
        }
    )

@app.get("/questions")
def get_questions_page(request: Request, group_id: int = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    tasks = crud.get_tasks(db)
    subgroups = crud.get_task_subgroups(db)
    groups = crud.get_task_groups(db)
    
    is_admin = user.is_admin if user else False

    return templates.TemplateResponse("question.html", {
        "request": request,
        "tasks": tasks,
        "subgroups": subgroups,
        "groups": groups,
        "group_id": group_id,
        "is_admin": is_admin,
    })


@app.get("/question/{task_id}")
def get_question_detail_page(request: Request, task_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница с детальным просмотром вопроса"""
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    # Получаем все вопросы той же подгруппы для навигации
    all_tasks = crud.get_tasks(db)
    subgroup_tasks = [t for t in all_tasks if t.task_subgroup_id == task.task_subgroup_id]
    subgroup_tasks.sort(key=lambda x: x.id)
    
    # Находим текущий индекс
    current_index = next((i for i, t in enumerate(subgroup_tasks) if t.id == task_id), -1)
    
    # Определяем предыдущий и следующий вопросы
    prev_task = subgroup_tasks[current_index - 1] if current_index > 0 else None
    next_task = subgroup_tasks[current_index + 1] if current_index < len(subgroup_tasks) - 1 else None
    
    subgroups = crud.get_task_subgroups(db)
    groups = crud.get_task_groups(db)
    is_admin = user.is_admin if user else False

    return templates.TemplateResponse("question_detail.html", {
        "request": request,
        "task": task,
        "subgroups": subgroups,
        "groups": groups,
        "is_admin": is_admin,
        "prev_task": prev_task,
        "next_task": next_task,
        "current_user": user,
    })

@app.get("/add-question")
def add_question_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница для добавления нового вопроса - только для админов"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут добавлять вопросы"
        )
    
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
        "is_admin": True,
    })

@app.post("/api/questions")
def create_question_api(task: TaskCreate, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    """API endpoint для создания вопроса - только для админов"""
    try:
        new_task = crud.create_task(db, task, created_by=user.id)
        return {"message": "Вопрос успешно добавлен", "task_id": new_task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/questions/{task_id}")
def get_question_api(task_id: int, db: Session = Depends(get_db)):
    """API endpoint для получения вопроса по ID"""
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return task

@app.put("/api/questions/{task_id}")
def update_question_api(task_id: int, task_update: TaskCreate, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    """API endpoint для обновления вопроса - только для админов"""
    try:
        updated_task = crud.update_task(db, task_id, task_update)
        if not updated_task:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        return {"message": "Вопрос успешно обновлен", "task_id": updated_task.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/questions/{task_id}")
def delete_question_api(task_id: int, db: Session = Depends(get_db), user: models.User = Depends(require_admin)):
    """API endpoint для удаления вопроса - только для админов"""
    try:
        success = crud.delete_task(db, task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        return {"message": "Вопрос успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manage-questions")
def manage_questions_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Единая страница для редактирования и удаления вопросов - только для админов"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут управлять вопросами"
        )
    
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
    
    tasks = crud.get_tasks(db)

    return templates.TemplateResponse("manage_questions.html", {
        "request": request,
        "subgroups": subgroups_data,
        "groups": groups_data,
        "tasks": tasks,
        "is_admin": True,
    })


@app.get("/edit-question")
def edit_question_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница для выбора вопроса на редактирование - только для админов"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут редактировать вопросы"
        )
    
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
    
    tasks = crud.get_tasks(db)

    return templates.TemplateResponse("edit_question.html", {
        "request": request,
        "subgroups": subgroups_data,
        "groups": groups_data,
        "tasks": tasks,
        "task_id": None,  # Нет выбранного вопроса
        "is_admin": True,
    })


@app.get("/edit-question/{task_id}")
def edit_question_page_with_id(request: Request, task_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница для редактирования конкретного вопроса - только для админов"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут редактировать вопросы"
        )
    
    # Проверяем существование вопроса
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
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

    return templates.TemplateResponse("edit_question.html", {
        "request": request,
        "subgroups": subgroups_data,
        "groups": groups_data,
        "task_id": task_id,
        "is_admin": True,
    })


@app.get("/delete-question")
def delete_question_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница для выбора вопроса на удаление - только для админов"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут удалять вопросы"
        )
    
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
    
    tasks = crud.get_tasks(db)

    return templates.TemplateResponse("delete_question.html", {
        "request": request,
        "subgroups": subgroups_data,
        "groups": groups_data,
        "tasks": tasks,
        "task_id": None,  # Нет выбранного вопроса
        "is_admin": True,
    })


@app.get("/delete-question/{task_id}")
def delete_question_page_with_id(request: Request, task_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница для удаления конкретного вопроса - только для админов"""
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут удалять вопросы"
        )
    
    # Проверяем существование вопроса
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
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

    return templates.TemplateResponse("delete_question.html", {
        "request": request,
        "subgroups": subgroups_data,
        "groups": groups_data,
        "task_id": task_id,
        "is_admin": True,
    })

# Authentication endpoints
@app.get("/login")
def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/login")
def api_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """API endpoint для входа"""
    user = crud.get_user_by_username(db, username=username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    response = JSONResponse({"message": "Успешный вход", "is_admin": user.is_admin})
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=1800, samesite="lax")
    return response

@app.post("/api/logout")
def api_logout():
    """API endpoint для выхода"""
    response = JSONResponse({"message": "Успешный выход"})
    response.delete_cookie(key="access_token")
    return response

@app.get("/register")
def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/api/register")
def api_register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """API endpoint для регистрации"""
    # Проверяем, существует ли пользователь
    existing_user = crud.get_user_by_username(db, username=username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    
    # Создаем нового пользователя (первый пользователь становится админом)
    is_first_user = db.query(models.User).count() == 0
    user = crud.create_user(db, UserCreate(username=username, password=password, is_admin=is_first_user))
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    response = JSONResponse({"message": "Успешная регистрация", "is_admin": user.is_admin})
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=1800, samesite="lax")
    return response

@app.get("/profile")
def profile_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user_from_cookie)):
    """Страница профиля"""
    if not user:
        return RedirectResponse(url="/login")
    
    # Получаем аналитику по группам для пользователя
    analytics = crud.get_user_analytics_by_group(db, user.id)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": user,
        "is_admin": user.is_admin,
        "analytics": analytics,
    })


# API endpoints для прогресса знаний
@app.post("/api/question-progress")
def update_question_progress_api(
    progress_data: QuestionProgressCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie)
):
    """API endpoint для обновления статуса знания вопроса"""
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    try:
        # Конвертируем статус из строки в enum
        status = models.KnowledgeStatus(progress_data.status.value)
        progress = crud.update_question_progress(db, user.id, progress_data.task_id, status)
        return {"message": "Статус обновлен", "progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/question-progress/{task_id}")
def get_question_progress_api(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie)
):
    """API endpoint для получения статуса знания вопроса"""
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    progress = crud.get_or_create_question_progress(db, user.id, task_id)
    return progress


@app.get("/api/analytics/by-group")
def get_analytics_by_group_api(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie)
):
    """API endpoint для получения аналитики знаний по группам вопросов"""
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    analytics = crud.get_user_analytics_by_group(db, user.id)
    return analytics

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8080,
        reload=True
    )