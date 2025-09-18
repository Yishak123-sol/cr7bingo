# Set remaining_balance to zero for a user

from fastapi import APIRouter, Depends, HTTPException, status
from .. import models, oauth2, schemas

from motor.motor_asyncio import AsyncIOMotorDatabase
from .. import database, models
from app.database import get_db
from bson import ObjectId

router = APIRouter(tags=["Package Transaction"], prefix="/package")


@router.post("/{given_receiver_id}", status_code=status.HTTP_201_CREATED)
@router.post("/{given_receiver_id}", status_code=status.HTTP_201_CREATED)
async def create_package_transaction(
    given_receiver_id: str,
    package_transaction: schemas.PackageTransactionModel,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    receiver_user = await db[models.USERS_COLLECTION].find_one(
        {"_id": ObjectId(given_receiver_id)}
    )
    if not receiver_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receiver user not found",
        )
    if current_user["role"] == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This user role does not have permission to transfer pakcage",
        )
    if (
        current_user["remaining_balance"] < package_transaction.package_amount
        and current_user["role"] != "owner"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient balance",
        )
    if str(current_user["_id"]) == given_receiver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You cannot transfer to yourself",
        )
    sender_name = current_user["name"]
    receiver_name = receiver_user["name"]
    updated_sender_package_amount = (
        current_user["remaining_balance"] - package_transaction.package_amount
    )
    updated_receiver_package_amount = (
        receiver_user["remaining_balance"] + package_transaction.package_amount
    )
    total_balance = receiver_user["total_balance"] + package_transaction.package_amount
    await db[models.USERS_COLLECTION].update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {"remaining_balance": updated_sender_package_amount}},
    )
    await db[models.USERS_COLLECTION].update_one(
        {"_id": ObjectId(given_receiver_id)},
        {
            "$set": {
                "remaining_balance": updated_receiver_package_amount,
                "total_balance": total_balance,
            }
        },
    )
    new_package_transaction = package_transaction.dict()
    new_package_transaction["receiver_id"] = given_receiver_id
    new_package_transaction["sender_id"] = str(current_user["_id"])
    new_package_transaction["receiver_name"] = receiver_name
    new_package_transaction["sender_name"] = sender_name
    result = await db[models.PACKAGE_TRANSACTIONS_COLLECTION].insert_one(
        new_package_transaction
    )
    return {
        "message": "Pakcage Transaction Created Successfully",
        "package_transaction": str(result.inserted_id),
    }

    new_package_transaction = models.PackageTransaction(
        receiver_id=given_receiver_id,
        sender_id=current_user.id,
        receiver_name=receiver_name,
        sender_name=sender_name,
        **package_transaction.dict(),
    )

    # update user total and remaining balance
    db.add(new_package_transaction)
    db.commit()
    db.refresh(new_package_transaction)

    return {
        "message": "Pakcage Transaction Created Successfully",
        "package_transaction": new_package_transaction,
    }


@router.get("/")
async def get_package_transactions(
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
    cursor = db[models.PACKAGE_TRANSACTIONS_COLLECTION].find({})
    package_transaction = await cursor.to_list(length=100)
    if not package_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No package transaction found",
        )
    return package_transaction


@router.get("/my-package-transaction")
async def get_package_transaction_by_userid(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    cursor = db[models.PACKAGE_TRANSACTIONS_COLLECTION].find(
        {
            "$or": [
                {"receiver_id": str(current_user["_id"])},
                {"sender_id": str(current_user["_id"])},
            ]
        }
    )
    package_transaction = await cursor.to_list(length=100)
    if not package_transaction:
        raise HTTPException(
            status_code=404, detail="you don't have a package transaction yet."
        )
    return package_transaction


@router.get("/my/{id}")
async def get_package_transaction_by_userid(
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
            detail=f"User not found",
        )
    cursor = db[models.PACKAGE_TRANSACTIONS_COLLECTION].find({})
    package_transaction = await cursor.to_list(length=100)
    if not package_transaction:
        raise HTTPException(
            status_code=404, detail="There is no package transaction yet."
        )
    if user["role"] == "owner":
        return package_transaction
    user_transactions_cursor = db[models.PACKAGE_TRANSACTIONS_COLLECTION].find(
        {"$or": [{"receiver_id": id}, {"sender_id": id}]}
    )
    user_transactions = await user_transactions_cursor.to_list(length=100)
    if not user_transactions:
        raise HTTPException(
            status_code=404, detail="you don't have a package transaction yet."
        )
    return user_transactions


@router.post("/update_balance/{user_id}")
async def update_remaining_balance(
    user_id: str,
    amount: float,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await db[models.USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db[models.USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)}, {"$inc": {"remaining_balance": amount}}
    )
    updated_user = await db[models.USERS_COLLECTION].find_one(
        {"_id": ObjectId(user_id)}
    )
    return {
        "message": "Balance updated",
        "remaining_balance": (
            updated_user["remaining_balance"] if updated_user else None
        ),
    }


@router.post("/update_remaining_balance/{user_id}")
async def update_remaining_balance(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await db[models.USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db[models.USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)}, {"$set": {"remaining_balance": 0}}
    )
    return {
        "message": "Balance updated",
        "remaining_balance": 0,
    }
