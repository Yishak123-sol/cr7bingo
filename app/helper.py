import secrets
import string
from app import models

CHARSET = string.digits + string.ascii_lowercase


def generate_code(length=6):
    six_digit_random_number = "".join(secrets.choice(CHARSET) for _ in range(length))
    return six_digit_random_number


async def generate_unique_code(db):
    while True:
        code = generate_code()
        existing = await db[models.BINGO_CARDS_COLLECTION].find_one({"_id": code})
        if not existing:
            return code
