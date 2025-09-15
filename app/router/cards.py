from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, oauth2, helper
from app.database import get_db
from app.schemas import MultipleBingoCardsCreate
from .. import schemas

router = APIRouter(prefix="/cards", tags=["Bingo Cards"])


@router.post("/")
def get_bingo_cards_byId(
    bingo_card: schemas.BingoCardFetch, db: Session = Depends(get_db)
):

    bingo_cards = (
        db.query(models.BingoCard)
        .filter(models.BingoCard.id == bingo_card.bingo_card_code)
        .first()
    )

    if not bingo_cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bingo card not found",
        )

    return bingo_cards


@router.post("/bingo_cards/")
def create_bingo_cards(
    bingo_cards: MultipleBingoCardsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    id = bingo_cards.id
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found",
        )
    card = db.query(models.BingoCard).filter(models.BingoCard.owner_id == id).first()

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
        card.card_data = new_card_data
        db.commit()
        card_id_to_set = card.id
    else:
        new_bingo_card = models.BingoCard(
            id=card_id, owner_id=id, card_data=new_card_data
        )
        db.add(new_bingo_card)
        db.commit()
        card_id_to_set = card_id

    user.bingo_card_code = card_id_to_set
    db.commit()

    return created_cards
