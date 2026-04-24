from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class KnowledgeStatusEnum(str, Enum):
    """Статусы знания вопроса"""
    KNOW = "know"
    ALMOST_KNOW = "almost_know"
    DONT_KNOW = "dont_know"

# === User schemas ===
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# === Progress schemas ===
class QuestionProgressBase(BaseModel):
    question_id: int
    status: KnowledgeStatusEnum

class QuestionProgressCreate(QuestionProgressBase):
    pass

class QuestionProgressUpdate(BaseModel):
    status: KnowledgeStatusEnum

class QuestionProgress(QuestionProgressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProgressSummary(BaseModel):
    """Сводка прогресса по группе вопросов"""
    group_id: int
    group_name: str
    total_questions: int
    know_count: int
    almost_know_count: int
    dont_know_count: int
    progress_percentage: float

class UserProgressSummary(BaseModel):
    """Общий прогресс пользователя"""
    user_id: int
    username: str
    total_questions: int
    know_count: int
    almost_know_count: int
    dont_know_count: int
    groups: list[ProgressSummary]

# === Task schemas ===
class TaskGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    image: Optional[str] = None

class TaskGroup(TaskGroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TaskSubgroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_group_id: int

class TaskSubgroup(TaskSubgroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    question: str
    answer: str
    failed_answer: Optional[str] = None
    description: Optional[str] = None
    task_subgroup_id: int

class Task(TaskBase):
    id: int
    task_subgroup: TaskSubgroup

    class Config:
        from_attributes = True

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    failed_answer: Optional[str] = None
    description: Optional[str] = None
    task_subgroup_id: Optional[int] = None

class TaskWithProgress(Task):
    """Вопрос со статусом прогресса для текущего пользователя"""
    user_status: Optional[KnowledgeStatusEnum] = None