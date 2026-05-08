from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class KnowledgeStatus(enum.Enum):
    KNOW = "know"
    ALMOST_KNOW = "almost_know"
    DONT_KNOW = "dont_know"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship с задачами (кто создал)
    tasks = relationship("Tasks", back_populates="creator")
    
    # Relationship с прогрессом знаний
    question_progress = relationship("QuestionProgress", back_populates="user", cascade="all, delete-orphan")

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
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationship with TaskSubgroups
    task_subgroup = relationship("TaskSubgroups", back_populates="tasks")
    
    # Relationship with User
    creator = relationship("User", back_populates="tasks")
    
    # Relationship с прогрессом знаний
    progress = relationship("QuestionProgress", back_populates="task", cascade="all, delete-orphan")


class QuestionProgress(Base):
    __tablename__ = 'question_progress'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    status = Column(SQLEnum(KnowledgeStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="question_progress")
    task = relationship("Tasks", back_populates="progress")