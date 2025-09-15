from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import database
from .. import models, utils, oauth2, schemas

router = APIRouter(tags=["Authentication"])


@router.post("/login", status_code=status.HTTP_201_CREATED)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.phone == user_credentials.username)
        .first()
    )

    if not user:
        print("User not found")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid Credentials",
        )

    if not utils.verify_password(user_credentials.password, user.password):
        print("Invalid password")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials"
        )

    access_token = oauth2.create_access_token(
        data={"user_id": user.id, "role": user.role.value}
    )
    bingo_card_code = user.bingo_card_code or ""

    bingo_card = None
    if bingo_card_code:
        bingo_card = (
            db.query(models.BingoCard)
            .filter(models.BingoCard.id == bingo_card_code)
            .first()
        )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "bingo_cards": bingo_card or [],
    }
