from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import enum

class Role(str, enum.Enum):
    manager = "manager"
    superagent = "superagent"
    owner = "owner"
    user = "user"



USERS_COLLECTION = "users"
GAME_TRANSACTIONS_COLLECTION = "game_transactions"
PACKAGE_TRANSACTIONS_COLLECTION = "package_transactions"
BINGO_CARDS_COLLECTION = "bingo_cards"
STORED_DATA_COLLECTION = "stored_data"

class UserModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str]
    phone: str
    password: str
    city: Optional[str]
    region: Optional[str]
    role: Role
    remaining_balance: float
    total_balance: float
    profile_picture: Optional[str]
    created_by: Optional[str]
    bingo_card_code: Optional[str]
    parent_id: Optional[str]
    created_at: Optional[str]



class GameTransactionModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    bet_amount: int
    game_type: str
    number_of_cards: int
    dedacted_amount: int
    remaining_balance: float
    total_balance: float
    owner_id: str
    owner_name: str
    created_at: Optional[str]



class PackageTransactionModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    sender_id: str
    receiver_id: str
    receiver_name: str
    sender_name: str
    package_amount: int
    created_at: Optional[str]



class BingoCardModel(BaseModel):
    id: str = Field(..., alias="_id")
    owner_id: str
    card_data: Dict
    created_at: Optional[str]



class StoredDataModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    data: Dict
    user_id: str
