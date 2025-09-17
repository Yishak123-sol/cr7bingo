from fastapi import APIRouter, Depends, HTTPException, status
from .. import models, oauth2, schemas, utils
from ..database import get_db
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

router = APIRouter(tags=["User"], prefix="/user")


@router.post("/fake", status_code=status.HTTP_201_CREATED)
@router.post("/fake", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    db_user = await db[models.USERS_COLLECTION].find_one({"phone": user.phone})
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    hashed_password = utils.hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["role"] = user.role
    user_dict["remaining_balance"] = user.remaining_balance or 0.0
    user_dict["total_balance"] = 0.0
    result = await db[models.USERS_COLLECTION].insert_one(user_dict)
    return {"message": "User created successfully", "user_id": str(result.inserted_id)}


@router.post("/", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user["role"] == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to create a user",
        )
    if current_user["role"] == "superagent" and user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Superagent does not have permission to create a owner, Manager and Superagent",
        )
    if current_user["role"] == "manager" and (
        user.role == "manager" or user.role == "owner"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Manager does not have permission to create a owner or Manager",
        )
    db_user = await db[models.USERS_COLLECTION].find_one({"phone": user.phone})
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    hashed_password = utils.hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["role"] = user.role
    user_dict["remaining_balance"] = user.remaining_balance or 0.0
    user_dict["total_balance"] = 0.0
    user_dict["created_by"] = str(current_user["_id"])
    result = await db[models.USERS_COLLECTION].insert_one(user_dict)
    return {"message": "User created successfully", "user_id": str(result.inserted_id)}


@router.get("/", response_model=List[schemas.UserOut])
@router.get("/", response_model=List[schemas.UserOut])
async def get_all_user(
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
            detail=f"User does not have permission to get all Users",
        )
    users_cursor = db[models.USERS_COLLECTION].find({"role": "user"})
    users = await users_cursor.to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Users found",
        )
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
    return users


@router.get("/all-role-users", response_model=List[schemas.UserOut])
async def get_all_role_user(
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
            detail=f"User does not have permission to get all Users",
        )
    users_cursor = db[models.USERS_COLLECTION].find({})
    users = await users_cursor.to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Users found",
        )
    # Convert _id to id for each user
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
    return users


@router.get("/me", response_model=schemas.UserOut)
@router.get("/me", response_model=schemas.UserOut)
async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    user = await db[models.USERS_COLLECTION].find_one(
        {"_id": ObjectId(current_user["_id"])}
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.get("/managers", response_model=List[schemas.UserOut])
@router.get("/managers", response_model=List[schemas.UserOut])
async def get_all_managers(
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
            detail=f"User does not have permission to get all Managers",
        )
    users_cursor = db[models.USERS_COLLECTION].find({"role": "manager"})
    users = await users_cursor.to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Managers found",
        )
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
    return users


@router.get("/superagents", response_model=List[schemas.UserOut])
@router.get("/superagents", response_model=List[schemas.UserOut])
async def get_all_superagents(
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
            detail=f"User does not have permission to get all Superagents",
        )
    users_cursor = db[models.USERS_COLLECTION].find({"role": "superagent"})
    users = await users_cursor.to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Superagents found",
        )
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
    return users


@router.get("/child", response_model=List[schemas.UserOut])
@router.get("/child", response_model=List[schemas.UserOut])
async def get_users_created_by_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    users_cursor = db[models.USERS_COLLECTION].find(
        {"parent_id": str(current_user["_id"])}
    )
    users = await users_cursor.to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found created by the current user",
        )
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
    return users


@router.get("/child/superagent/{id}", response_model=List[schemas.UserOut])
@router.get("/child/superagent/{id}", response_model=List[schemas.UserOut])
async def get_users_created_by_user_id(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db[models.USERS_COLLECTION].find_one({"_id": ObjectId(id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found",
        )
    users_cursor = db[models.USERS_COLLECTION].find({"role": "superagent"})
    users = await users_cursor.to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )
    for user_doc in users:
        user_doc["id"] = str(user_doc["_id"])
        del user_doc["_id"]
    if user["role"] == "owner":
        return users
    all_users_cursor = db[models.USERS_COLLECTION].find(
        {"parent_id": id, "role": "superagent"}
    )
    all_users = await all_users_cursor.to_list(length=100)
    if not all_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )
    for user_doc in all_users:
        user_doc["id"] = str(user_doc["_id"])
        del user_doc["_id"]
    return all_users
