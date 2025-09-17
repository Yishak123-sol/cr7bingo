from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from .. import models, oauth2, helper
from app.database import get_db
from app.schemas import MultipleBingoCardsCreate
from .. import schemas
from bson import ObjectId

router = APIRouter(prefix="/cards", tags=["Bingo Cards"])


@router.post("/")
@router.post("/")
async def get_bingo_cards_byId(
    bingo_card: schemas.BingoCardFetch, db: AsyncIOMotorDatabase = Depends(get_db)
):
    bingo_card_doc = await db[models.BINGO_CARDS_COLLECTION].find_one({"_id": bingo_card.bingo_card_code})
    if not bingo_card_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bingo card not found",
        )
    return bingo_card_doc


@router.post("/bingo_cards/")
@router.post("/bingo_cards/")
async def create_bingo_cards(
    bingo_cards: MultipleBingoCardsCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(oauth2.get_current_user),
):
    id = bingo_cards.id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    user = await db[models.USERS_COLLECTION].find_one({"_id": ObjectId(id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found",
        )
    card = await db[models.BINGO_CARDS_COLLECTION].find_one({"owner_id": id})

    created_cards = []
    for card_data in bingo_cards.cards:
        card_dict = {
            "B": card_data.B,
            "I": card_data.I,
            "N": card_data.N,
            "G": card_data.G,
            "O": card_data.O,
            "cardNumber": card_data.cardNumber,
        }
        created_cards.append(card_dict)

    new_card_data = {"cards": created_cards}
    card_id = helper.generate_unique_code(db)

    if card:
        await db[models.BINGO_CARDS_COLLECTION].update_one(
            {"_id": card["_id"]}, {"$set": {"card_data": new_card_data}}
        )
        card_id_to_set = card["_id"]
    else:
        new_bingo_card = {
            "_id": card_id,
            "owner_id": id,
            "card_data": new_card_data,
        }
        await db[models.BINGO_CARDS_COLLECTION].insert_one(new_bingo_card)
        card_id_to_set = card_id

    await db[models.USERS_COLLECTION].update_one(
        {"_id": ObjectId(id)}, {"$set": {"bingo_card_code": card_id_to_set}}
    )

    return created_cards
