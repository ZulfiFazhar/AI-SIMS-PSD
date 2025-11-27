# Model Directory

This folder can be used for Data Transfer Objects (DTOs), Object-Relational Mapping (ORM) models, or any domain-specific models that represent the core entities of your application.

## Examples

1. **SQLAlchemy ORM Model**:

   ```python
   from sqlalchemy import Column, Integer, String, DateTime
   from sqlalchemy.ext.declarative import declarative_base

   Base = declarative_base()

   class User(Base):
       __tablename__ = "users"

       id = Column(Integer, primary_key=True)
       username = Column(String(50), unique=True)
       email = Column(String(100))
       created_at = Column(DateTime)
   ```

2. **Pydantic DTO Model**:

   ```python
   from pydantic import BaseModel
   from typing import Optional

    class UserCreateDTO(BaseModel):
    username: str
    email: str
    password: str

    class UserResponseDTO(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

   ```

3. **Domain Model**:

   ```python
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class User:
        id: int
        username: str
        email: str

    @dataclass
    class UserList:
        users: List[User]

    @dataclass
    class AIAnalysisResult:
        confidence_score: float
        predictions: List[str]
        processing_time: float
        model_version: str
   ```

These models can be imported and used throughout your application, including in services, API routes, and business logic layers.
