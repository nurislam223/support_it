from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator
import re


class EmailType(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValueError("Invalid email format")
        return value