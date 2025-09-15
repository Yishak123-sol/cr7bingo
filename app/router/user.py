from fastapi import APIRouter, Depends, HTTPException, status
from .. import models, oauth2, schemas
from sqlalchemy.orm import Session
from .. import database, models, utils
from typing import List

router = APIRouter(tags=["User"], prefix="/user")


@router.post("/fake", status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate = Depends(),
    db: Session = Depends(database.get_db),
):

    db_user = db.query(models.User).filter(models.User.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Hash the password
    hashed_password = utils.hash_password(user.password)

    new_user = models.User(
        phone=user.phone,
        password=hashed_password,
        name=user.name,
        role=user.role,
        city=user.city,
        region=user.region,
        remaining_balance=user.remaining_balance or 0.0,
        total_balance=0.0,
        profile_picture=user.profile_picture,
        parent_id=user.parent_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "phone": new_user.phone}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if current_user.role.value == "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to create a user",
        )

    if current_user.role.value == "superagent" and user.role.value != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Superagent does not have permission to create a owner, Manager and Superagent",
        )

    if current_user.role.value == "manager" and (
        user.role.value == "manager" or user.role.value == "owner"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Manager does not have permission to create a owner or Manager",
        )

    db_user = db.query(models.User).filter(models.User.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    hashed_password = utils.hash_password(user.password)

    new_user = models.User(
        phone=user.phone,
        password=hashed_password,
        name=user.name,
        role=user.role,
        city=user.city,
        region=user.region,
        remaining_balance=user.remaining_balance or 0.0,
        total_balance=0.0,
        profile_picture=user.profile_picture,
        parent_id=user.parent_id,
        created_by=current_user.id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}


@router.get("/", response_model=List[schemas.UserOut])
def get_all_user(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Users",
        )
    users = db.query(models.User).filter(models.User.role == models.Role.user).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Users found",
        )

    return users


@router.get("/all-role-users", response_model=List[schemas.UserOut])
def get_all_role_user(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Users",
        )
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Users found",
        )

    return users


@router.get("/me", response_model=schemas.UserOut)
def get_current_user(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.get("/managers", response_model=List[schemas.UserOut])
def get_all_managers(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Managers",
        )

    users = db.query(models.User).filter(models.User.role == models.Role.manager).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Managers found",
        )

    return users


@router.get("/superagents", response_model=List[schemas.UserOut])
def get_all_superagents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role.value != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have permission to get all Superagents",
        )

    users = (
        db.query(models.User).filter(models.User.role == models.Role.superagent).all()
    )
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Superagents found",
        )

    return users


@router.get("/child", response_model=List[schemas.UserOut])
def get_users_created_by_current_user(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users = db.query(models.User).filter(models.User.parent_id == current_user.id).all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found created by the current user",
        )

    return users


@router.get("/child/superagent/{id}", response_model=List[schemas.UserOut])
def get_users_created_by_user_id(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found",
        )

    users = (
        db.query(models.User).filter(models.User.role == models.Role.superagent).all()
    )

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )

    if user.role.value == "owner":
        return users

    all_users = (
        db.query(models.User)
        .filter(models.User.parent_id == id, models.User.role == models.Role.superagent)
        .all()
    )

    if not all_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No users found created by user with id {id}",
        )

    return all_users
