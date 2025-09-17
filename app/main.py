
from fastapi import Depends, FastAPI
from app.oauth2 import verify_token
from app.router import auth, user, game_transaction, package_transaction, cards

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(package_transaction.router)
app.include_router(game_transaction.router)
app.include_router(cards.router)


@app.get("/")
def root():
    return {"message": "Hello World......"}
