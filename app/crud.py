from sqlalchemy.orm import Session, joinedload
from app.models import Tasks, TaskSubgroups, TaskGroups, User, QuestionProgress, KnowledgeStatus
from app.schemas import TaskCreate, TaskUpdate, UserCreate, QuestionProgressCreate
from typing import List, Optional
from app.auth import get_password_hash

def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[Tasks]:
    return db.query(Tasks).options(
        joinedload(Tasks.task_subgroup).joinedload(TaskSubgroups.task_group)
    ).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int) -> Optional[Tasks]:
    return db.query(Tasks).options(
        joinedload(Tasks.task_subgroup).joinedload(TaskSubgroups.task_group)
    ).filter(Tasks.id == task_id).first()

def get_tasks_by_subgroup(db: Session, subgroup_id: int) -> List[Tasks]:
    return db.query(Tasks).options(
        joinedload(Tasks.task_subgroup).joinedload(TaskSubgroups.task_group)
    ).filter(Tasks.task_subgroup_id == subgroup_id).all()

def get_tasks_by_group(db: Session, group_id: int) -> List[Tasks]:
    return db.query(Tasks).options(
        joinedload(Tasks.task_subgroup).joinedload(TaskSubgroups.task_group)
    ).filter(TaskSubgroups.task_group_id == group_id).join(TaskSubgroups).all()

def get_task_subgroups(db: Session) -> List[TaskSubgroups]:
    return db.query(TaskSubgroups).all()

def get_task_subgroup(db: Session, subgroup_id: int) -> Optional[TaskSubgroups]:
    return db.query(TaskSubgroups).filter(TaskSubgroups.id == subgroup_id).first()

def get_task_groups(db: Session) -> List[TaskGroups]:
    return db.query(TaskGroups).all()

def create_task(db: Session, task: TaskCreate, created_by: int = None) -> Tasks:
    db_task = Tasks(**task.dict(), created_by=created_by)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Tasks]:
    db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if db_task:
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int) -> bool:
    db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password, is_admin=user.is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_is_admin(db: Session, user_id: int, is_admin: bool) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.is_admin = is_admin
        db.commit()
        db.refresh(db_user)
    return db_user


# QuestionProgress CRUD operations
def get_or_create_question_progress(db: Session, user_id: int, task_id: int) -> Optional[QuestionProgress]:
    """Получить или создать прогресс для вопроса"""
    progress = db.query(QuestionProgress).filter(
        QuestionProgress.user_id == user_id,
        QuestionProgress.task_id == task_id
    ).first()
    
    if not progress:
        progress = QuestionProgress(
            user_id=user_id,
            task_id=task_id,
            status=KnowledgeStatus.DONT_KNOW
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return progress


def update_question_progress(db: Session, user_id: int, task_id: int, status: KnowledgeStatus) -> Optional[QuestionProgress]:
    """Обновить статус знания вопроса"""
    progress = db.query(QuestionProgress).filter(
        QuestionProgress.user_id == user_id,
        QuestionProgress.task_id == task_id
    ).first()
    
    if not progress:
        progress = QuestionProgress(
            user_id=user_id,
            task_id=task_id,
            status=status
        )
        db.add(progress)
    else:
        progress.status = status
    
    db.commit()
    db.refresh(progress)
    return progress


def get_user_analytics_by_group(db: Session, user_id: int) -> List[dict]:
    """Получить аналитику знаний пользователя по группам вопросов"""
    from sqlalchemy import func
    
    # Получаем все группы
    groups = db.query(TaskGroups).all()
    
    analytics = []
    for group in groups:
        # Получаем все вопросы в этой группе
        group_tasks = db.query(Tasks).join(TaskSubgroups).filter(
            TaskSubgroups.task_group_id == group.id
        ).all()
        
        total_questions = len(group_tasks)
        
        if total_questions == 0:
            continue
        
        # Получаем прогресс пользователя по этим вопросам
        task_ids = [task.id for task in group_tasks]
        progress_list = db.query(QuestionProgress).filter(
            QuestionProgress.user_id == user_id,
            QuestionProgress.task_id.in_(task_ids)
        ).all()
        
        know_count = sum(1 for p in progress_list if p.status == KnowledgeStatus.KNOW)
        almost_know_count = sum(1 for p in progress_list if p.status == KnowledgeStatus.ALMOST_KNOW)
        dont_know_count = sum(1 for p in progress_list if p.status == KnowledgeStatus.DONT_KNOW)
        
        analytics.append({
            "group_id": group.id,
            "group_name": group.name,
            "total_questions": total_questions,
            "know_count": know_count,
            "almost_know_count": almost_know_count,
            "dont_know_count": dont_know_count
        })
    
    return analytics