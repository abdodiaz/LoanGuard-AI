import os
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 1. Configuration dial l-Connection
# West Docker, l-host houwa "db" (smit l-service f docker-compose)
# Berra dial Docker (PC), l-host houwa "localhost" o l-port 5433
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://diazpg:diazpg123@db:5432/loan_db"
)

# 2. Setup dial SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Model dial l-Utilisateurs (Users)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")  # 'admin' wala 'user'

# 4. Model dial l-Prédictions (History)
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_data = Column(JSON)  # Khbe3 l-form data kamla hna
    prediction = Column(String) # 'Approved' wala 'Rejected'
    probability = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# 5. Création automatique dial l-tables
# Had l-ligne hiya li kat-creer users o predictions f PostgreSQL mli kiy-bda l-app
def init_models():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_models()
    print("Tables created successfully!")