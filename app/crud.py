from sqlalchemy.orm import Session, joinedload
from models import Tasks, TaskSubgroups, TaskGroups, User, QuestionProgress, KnowledgeStatus
from schemas import TaskCreate, TaskUpdate, UserCreate, UserUpdate, QuestionProgressCreate, QuestionProgressUpdate
from typing import List, Optional
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === User CRUD operations ===
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        if 'password' in update_data and update_data['password']:
            update_data['hashed_password'] = pwd_context.hash(update_data.pop('password'))
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# === Question Progress CRUD operations ===
def get_question_progress(db: Session, user_id: int, question_id: int) -> Optional[QuestionProgress]:
    return db.query(QuestionProgress).filter(
        QuestionProgress.user_id == user_id,
        QuestionProgress.question_id == question_id
    ).first()

def get_user_progress(db: Session, user_id: int) -> List[QuestionProgress]:
    return db.query(QuestionProgress).filter(QuestionProgress.user_id == user_id).all()

def get_or_create_progress(db: Session, user_id: int, question_id: int) -> QuestionProgress:
    progress = get_question_progress(db, user_id, question_id)
    if not progress:
        progress = QuestionProgress(
            user_id=user_id,
            question_id=question_id,
            status=KnowledgeStatus.DONT_KNOW
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress

def update_question_progress(db: Session, user_id: int, question_id: int, status: KnowledgeStatus) -> QuestionProgress:
    progress = get_or_create_progress(db, user_id, question_id)
    progress.status = status
    progress.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(progress)
    return progress

def get_user_progress_summary(db: Session, user_id: int) -> dict:
    """Получить сводку прогресса пользователя по группам вопросов"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    # Получаем все вопросы с их группами
    all_tasks = db.query(Tasks).join(TaskSubgroups).join(TaskGroups).all()
    
    # Получаем прогресс пользователя
    user_progress = {p.question_id: p.status for p in get_user_progress(db, user_id)}
    
    # Группируем по группам вопросов
    groups_data = {}
    for task in all_tasks:
        group = task.task_subgroup.task_group
        if group.id not in groups_data:
            groups_data[group.id] = {
                'group_id': group.id,
                'group_name': group.name,
                'total': 0,
                'know': 0,
                'almost_know': 0,
                'dont_know': 0
            }
        
        groups_data[group.id]['total'] += 1
        status = user_progress.get(task.id, KnowledgeStatus.DONT_KNOW)
        if status == KnowledgeStatus.KNOW:
            groups_data[group.id]['know'] += 1
        elif status == KnowledgeStatus.ALMOST_KNOW:
            groups_data[group.id]['almost_know'] += 1
        else:
            groups_data[group.id]['dont_know'] += 1
    
    # Формируем результат
    total_questions = len(all_tasks)
    know_count = sum(g['know'] for g in groups_data.values())
    almost_know_count = sum(g['almost_know'] for g in groups_data.values())
    dont_know_count = sum(g['dont_know'] for g in groups_data.values())
    
    groups_summary = []
    for group_data in groups_data.values():
        progress_pct = (group_data['know'] / group_data['total'] * 100) if group_data['total'] > 0 else 0
        groups_summary.append({
            'group_id': group_data['group_id'],
            'group_name': group_data['group_name'],
            'total_questions': group_data['total'],
            'know_count': group_data['know'],
            'almost_know_count': group_data['almost_know'],
            'dont_know_count': group_data['dont_know'],
            'progress_percentage': round(progress_pct, 2)
        })
    
    return {
        'user_id': user.id,
        'username': user.username,
        'total_questions': total_questions,
        'know_count': know_count,
        'almost_know_count': almost_know_count,
        'dont_know_count': dont_know_count,
        'groups': groups_summary
    }

# === Task CRUD operations (existing) ===
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
    ).join(TaskSubgroups).filter(
        TaskSubgroups.task_group_id == group_id
    ).all()

def get_task_subgroups(db: Session) -> List[TaskSubgroups]:
    return db.query(TaskSubgroups).options(
        joinedload(TaskSubgroups.task_group)
    ).all()

def get_task_subgroups_by_group(db: Session, group_id: int) -> List[TaskSubgroups]:
    """Получить подгруппы конкретной группы"""
    return db.query(TaskSubgroups).filter(
        TaskSubgroups.task_group_id == group_id
    ).all()

def get_task_subgroup(db: Session, subgroup_id: int) -> Optional[TaskSubgroups]:
    return db.query(TaskSubgroups).options(
        joinedload(TaskSubgroups.task_group)
    ).filter(TaskSubgroups.id == subgroup_id).first()

def get_task_groups(db: Session) -> List[TaskGroups]:
    return db.query(TaskGroups).options(
        joinedload(TaskGroups.task_subgroups)
    ).all()

def get_task_group(db: Session, group_id: int) -> Optional[TaskGroups]:
    """Получить конкретную группу"""
    return db.query(TaskGroups).options(
        joinedload(TaskGroups.task_subgroups)
    ).filter(TaskGroups.id == group_id).first()

def create_task(db: Session, task: TaskCreate) -> Tasks:
    db_task = Tasks(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Tasks]:
    db_task = db.query(Tasks).filter(Tasks.id == task_id).first()
    if db_task:
        update_data = task_update.model_dump(exclude_unset=True)
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

def get_task_count_by_group(db: Session, group_id: int) -> int:
    """Получить количество вопросов в группе"""
    from sqlalchemy import func
    return db.query(func.count(Tasks.id)).join(TaskSubgroups).filter(
        TaskSubgroups.task_group_id == group_id
    ).scalar()

def get_task_count_by_subgroup(db: Session, subgroup_id: int) -> int:
    """Получить количество вопросов в подгруппе"""
    from sqlalchemy import func
    return db.query(func.count(Tasks.id)).filter(
        Tasks.task_subgroup_id == subgroup_id
    ).scalar()
