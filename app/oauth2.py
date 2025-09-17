from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from sqlalchemy.orm import Session
import jwt
from app import schemas, database, models
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from app.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
# ACCESSTOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except jwt.PyJWTError:
        raise credentials_exception

    return token_data


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    user = await db[models.USERS_COLLECTION].find_one({"_id": ObjectId(token_data.id)})
    if not user:
        raise credentials_exception
    return user
