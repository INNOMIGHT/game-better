import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.riot import router as riot_router



load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "Innomight GameBetter API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
)


app.include_router(health_router)
app.include_router(users_router)
app.include_router(riot_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Innomight Gamebetter API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }