import bcrypt
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Numeric, Boolean
from custom_types import EmailType


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True )
    label = Column(String)
    question = Column(String)
    answer = Column(String)
    failed_answer = Column(String)
    description = Column(String)
    task_group_id = Column(Integer, ForeignKey("task_groups.id"))

    task_group = relationship("TaskGroups", back_populates="tasks")

class TaskGroups(Base):
    __tablename__ = "task_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    tasks = relationship("Tasks", back_populates="task_group")


class Users(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(EmailType)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    def set_password(self, password: str):
        """Хеширование пароля"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Проверка пароля"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

