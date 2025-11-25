from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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