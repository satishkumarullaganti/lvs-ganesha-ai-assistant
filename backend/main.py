from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.models import ChatRequest
from fastapi.staticfiles import StaticFiles
from backend.chat_service import get_ai_response
from backend.registration_service import registration 
from backend.annaprasada_service import annaprasada_service  
from backend.database.database import (
    create_tables,
    get_registrations,
    save_registration,
    save_annaprasada_booking 
)

# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="LVS Ganesha AI Assistant",
    version="2.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static") 
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
# Registration Model         
# ============================================
class RegistrationRequest(BaseModel):
    competition: str
    name: str
    block: str
    flat: str
    mobile: str
    age: str

# ============================================
# Register API               
# ============================================

@app.post("/register")
def register(data: RegistrationRequest):

    save_registration(
        name=data.name,
        block=data.block,
        flat_number=data.flat,
        mobile=data.mobile,
        age=int(data.age),
        competition=data.competition
    )

    return {
        "status": "success",
        "message": f"Registration successful for {data.name}"
    }

# ============================================
# Chat API
# ============================================

@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    # ==========================================
    # Continue Annaprasada Booking (if active)
    # ==========================================

    if annaprasada_service.active:

        return {
            "response": annaprasada_service.process_booking(message)
        }

    # ==========================================
    # Start Annaprasada Coupon Booking
    # ==========================================

    if "annaprasada" in message.lower():

        result = annaprasada_service.check_booking_status()

        return {
            "response": result["response"]
        }

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