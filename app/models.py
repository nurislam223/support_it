from sentry_sdk.tracing import SENTRY_TRACE_HEADER_NAME
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class TaskGroups(Base):
    __tablename__ = 'task_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    image = Column(String)

    # Relationship with TaskSubgroups
    task_subgroups = relationship("TaskSubgroups", back_populates="task_group")

class TaskSubgroups(Base):
    __tablename__ = 'task_subgroups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    task_group_id = Column(Integer, ForeignKey('task_groups.id'), nullable=False)  # ForeignKey
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with TaskGroups
    task_group = relationship("TaskGroups", back_populates="task_subgroups")

    # Relationship with Tasks (если есть)
    tasks = relationship("Tasks", back_populates="task_subgroup")

class Tasks(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(200), nullable=False)
    answer = Column(String, nullable=False)
    failed_answer = Column(String)
    description = Column(Text)
    task_subgroup_id = Column(Integer, ForeignKey('task_subgroups.id'), nullable=False)  # ForeignKey


    # Relationship with TaskSubgroups
    task_subgroup = relationship("TaskSubgroups", back_populates="tasks")