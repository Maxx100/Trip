
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
import hashlib
import logging
from database import create_user
from core.logger.logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Accounts Service")

class UserCreate(BaseModel):
    email: EmailStr
    password: str

@app.post("/create_user", status_code=status.HTTP_201_CREATED)
def create_new_user(user: UserCreate):
    logger.info(f"Received request to create user: {user.email}")
    
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()
    user_id = create_user(user.email, password_hash)
    
    if user_id:
        logger.info(f"User created: {user_id}")
        return {"status": "success", "user_id": user_id}
    else:
        logger.warning(f"Failed to create user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists or error occurred"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

