from sqlalchemy.orm import Session, joinedload
from models import Tasks, TaskSubgroups, TaskGroups
from schemas import TaskCreate, TaskUpdate
from typing import List, Optional

def get_tasks(db: Session, skip: int = 0, limit: int = 1000) -> List[Tasks]:
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
