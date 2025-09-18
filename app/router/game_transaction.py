from fastapi import APIRouter, Depends, HTTPException, status
from .. import models, oauth2, schemas
from motor.motor_asyncio import AsyncIOMotorDatabase
from .. import database, models
from app.database import get_db
from bson import ObjectId

router = APIRouter(tags=["Game Transaction"], prefix="/gamet")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_game_transaction(
    game_transaction: schemas.GameTransactionModel,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db[models.USERS_COLLECTION].find_one(
        {"_id": ObjectId(current_user["_id"])}
    )
    remain_balance = user["remaining_balance"]
    if remain_balance < game_transaction.dedacted_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You don't have enough balance to place this bet",
        )
    await db[models.USERS_COLLECTION].update_one(
        {"_id": ObjectId(current_user["_id"])},
        {
            "$set": {
                "remaining_balance": remain_balance - game_transaction.dedacted_amount
            }
        },
    )
    new_game_transaction = game_transaction.dict()
    new_game_transaction["remaining_balance"] = (
        remain_balance - game_transaction.dedacted_amount
    )
    new_game_transaction["total_balance"] = user["total_balance"]
    new_game_transaction["owner_id"] = str(current_user["_id"])
    new_game_transaction["owner_name"] = user["name"]
    result = await db[models.GAME_TRANSACTIONS_COLLECTION].insert_one(
        new_game_transaction
    )
    return {
        "message": "Game Transaction Created Successfully",
        "game_transaction": str(result.inserted_id),
    }


@router.get("/")
@router.get("/")
async def get_game_transactions(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user["role"] != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"you do not have permission to access this data",
        )
    cursor = db[models.GAME_TRANSACTIONS_COLLECTION].find({})
    game_transaction = await cursor.to_list(length=100)
    if not game_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No game transaction found",
        )
    return game_transaction


@router.get("/my/{id}")
@router.get("/my/{id}")
async def get_game_transaction_by_userid(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db[models.USERS_COLLECTION].find_one({"_id": ObjectId(id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    cursor = db[models.GAME_TRANSACTIONS_COLLECTION].find({})
    game_transaction = await cursor.to_list(length=100)
    if not game_transaction:
        raise HTTPException(status_code=404, detail="There is no game transaction yet.")
    if user["role"] == "owner":
        return game_transaction
    user_transactions_cursor = db[models.GAME_TRANSACTIONS_COLLECTION].find(
        {"owner_id": id}
    )
    user_transactions = await user_transactions_cursor.to_list(length=100)
    if not user_transactions:
        raise HTTPException(
            status_code=404, detail="you don't have a game transaction yet."
        )
    return user_transactions


@router.get("/my-game-transaction")
@router.get("/my-game-transaction")
async def get_game_transaction_by_userid(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_transactions_cursor = db[models.GAME_TRANSACTIONS_COLLECTION].find(
        {"owner_id": str(current_user["_id"])}
    )
    game_transaction = await user_transactions_cursor.to_list(length=100)
    if not game_transaction:
        raise HTTPException(
            status_code=404, detail="you don't have a game transaction yet."
        )
    return game_transaction
