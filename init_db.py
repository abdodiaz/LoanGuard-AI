import os
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 1. Configuration  l-Connection
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://diazpg:diazpg123@db:5432/loan_db"
)

# 2. Setup  SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Model  l-Utilisateurs (Users)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")  # 'admin' wala 'user'

# 4. Model Prédictions (History)
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_data = Column(JSON)  # Khbe3 l-form data kamla hna
    prediction = Column(String) # 'Approved' wala 'Rejected'
    probability = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_models()
    print("Tables created successfully!")