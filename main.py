import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pymongo import AsyncMongoClient

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "portfolio_db")

class ContactMessageIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=1, max_length=2000)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncMongoClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://aarushigautam.com",
        "https://www.aarushigautam.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/api/messages", status_code=201)
async def create_message(payload: ContactMessageIn):
    doc = {
        "name": payload.name.strip(),
        "email": payload.email.lower().strip(),
        "message": payload.message.strip(),
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = await app.mongodb.messages.insert_one(doc)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save message")

    return {"success": True, "id": str(result.inserted_id)}