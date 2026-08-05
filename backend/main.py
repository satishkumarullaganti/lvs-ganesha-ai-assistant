from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models import ChatRequest
from backend.chat_service import get_ai_response
from backend.registration_service import registration   
from backend.database.database import (
    create_tables,
    get_registrations,
    save_registration
)

# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="LVS Ganesha AI Assistant",
    version="2.0"
)

# ============================================
# Database Initialization
# ============================================

create_tables()

# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Home
# ============================================

@app.get("/")
def home():

    return {
        "message": "🙏 Welcome to LVS Ganesha AI Assistant V2"
    }

# ============================================
# About
# ============================================

@app.get("/about")
def about():

    return {
        "application": "LVS Ganesha AI Assistant",
        "version": "2.0",
        "developer": "Satish Kumar Ullaganti"
    }

# ============================================
# Chat API
# ============================================

@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    # -----------------------------
    # Start Registration
    # -----------------------------
    if not registration.active:

        if "register" in message.lower():

            return {
                "response": registration.start()
            }

    # -----------------------------
    # Continue Registration
    # -----------------------------
    if registration.active:

        return {
            "response": registration.process(message)
        }

    # -----------------------------
    # Normal AI Chat
    # -----------------------------
    reply = get_ai_response(message)

    return {
        "response": reply
    }

# ============================================
# View Registrations
# ============================================

@app.get("/registrations")
def registrations():

    rows = get_registrations()

    result = []

    for row in rows:

        result.append({

           "id": row[0],
    "name": row[1],
    "block": row[2],
    "flat_number": row[3],
    "mobile": row[4],
    "age": row[5],
    "competition": row[6],
    "created_at": row[7]

        })

    return result

