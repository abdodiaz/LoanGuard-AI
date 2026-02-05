import os
import pickle
import pandas as pd
from datetime import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

import init_db  # Database models o SessionLocal

# 1. Configuration & Security
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "diaz123")
ALGORITHM = "HS256"

# Logic dial l-DATABASE_URL:
# West Docker host khass i-koun "db". "localhost" k-i-khdem ghir ila lancyiti l-app bla Docker.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diazpg:diazpg123@db:5432/loan_db")

# Creer l-engine (DAROURI i-koun hna 9bel create_all)
engine = create_engine(DATABASE_URL)

# Automatic Table Creation
init_db.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="LoanGuard AI API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Model Loading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "notebooks", "model.pkl")

model = None
try:
    with open(model_path, "rb") as f:
        model = pickle.load(f)
except FileNotFoundError:
    print(f"⚠️ Error: Model not found at {model_path}")

# 3. Dependencies
def get_db():
    db = init_db.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.query(init_db.User).filter(init_db.User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")

# 4. Endpoints
@app.get("/")
def read_root():
    return FileResponse('static/login.html')

@app.post("/register")
def register(email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(init_db.User).filter(init_db.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    new_user = init_db.User(email=email, password=pwd_context.hash(password), role="user")
    db.add(new_user)
    db.commit()
    return {"message": "Utilisateur créé avec succès"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(init_db.User).filter(init_db.User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Identifiants incorrects")
    
    token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@app.post("/predict")
def predict(data: dict, current_user: init_db.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model ML machi khdam")

    mapping = {
        "Gender": {"Male": 1, "Female": 0},
        "Married": {"Yes": 1, "No": 0},
        "Education": {"Graduate": 1, "Not Graduate": 0},
        "Self_Employed": {"Yes": 1, "No": 0},
        "Property_Area": {"Urban": 2, "Semiurban": 1, "Rural": 0},
        "Dependents": {"0": 0, "1": 1, "2": 2, "3+": 3}
    }
    
    clean_data = data.copy()
    for key, val_map in mapping.items():
        if key in clean_data:
            clean_data[key] = val_map.get(clean_data[key], 0)

    df = pd.DataFrame([clean_data])
    
    try:
        pred_val = int(model.predict(df)[0])
        proba = f"{model.predict_proba(df)[0].max() * 100:.2f}%"
        result_text = "Approved" if pred_val == 1 else "Rejected"

        new_prediction = init_db.Prediction(
            user_id=current_user.id,
            input_data=data,
            prediction=result_text,
            probability=proba
        )
        db.add(new_prediction)
        db.commit()
        return {"prediction": result_text, "probability": proba}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history(u: init_db.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(init_db.Prediction).filter(init_db.Prediction.user_id == u.id).order_by(init_db.Prediction.created_at.desc()).limit(10).all()

@app.get("/admin/users")
def list_users(u: init_db.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if u.role != "admin": raise HTTPException(status_code=403, detail="Privilèges insuffisants")
    return db.query(init_db.User).all()

@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, u: init_db.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if u.role != "admin": raise HTTPException(status_code=403, detail="Privilèges insuffisants")
    user = db.query(init_db.User).filter(init_db.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}