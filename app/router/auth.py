from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from app.database import get_db
from .. import models, utils, oauth2, schemas
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore


router = APIRouter(tags=["Authentication"])


@router.post("/login", status_code=status.HTTP_201_CREATED)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user = await db[models.USERS_COLLECTION].find_one(
        {"phone": user_credentials.username}
    )
    if not user:
        print("User not found")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Credentials",
        )
    if not utils.verify_password(user_credentials.password, user["password"]):
        print("Invalid password")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials"
        )
    access_token = oauth2.create_access_token(
        data={"user_id": str(user["_id"]), "role": user["role"]}
    )
    bingo_card_code = user.get("bingo_card_code", "")
    bingo_card = None
    if bingo_card_code:
        bingo_card = await db[models.BINGO_CARDS_COLLECTION].find_one(
            {"_id": bingo_card_code}
        )
    user["_id"] = str(user["_id"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "bingo_cards": bingo_card or [],
    }
