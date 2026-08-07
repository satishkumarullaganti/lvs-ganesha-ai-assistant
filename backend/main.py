from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.models import ChatRequest
from fastapi.staticfiles import StaticFiles
from backend.chat_service import get_ai_response
from backend.registration_service import registration 
from backend.annaprasada_service import annaprasada_service  
from backend.donation_service import donation_service
from fastapi.responses import HTMLResponse
from backend.database.database import get_booking_by_coupon, mark_coupon_used
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
    # Continue Donation Flow (if active)
    # ==========================================

    if donation_service.active:

        return {
            "response": donation_service.process_donation(message)
        }

    # ==========================================
    # Start Donation Flow
    # ==========================================

    if "donation" in message.lower():

        return {
            "response": donation_service.start_donation()
        }

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
# Verify Annaprasada Coupon (Volunteer Scan)
# ============================================

@app.get("/verify/{coupon_id}", response_class=HTMLResponse)
def verify_coupon(coupon_id: str):

    booking = get_booking_by_coupon(coupon_id)

    if not booking:

        return """
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h1 style="color:#F44336;">⚠️ Invalid Coupon</h1>
        <p>This coupon ID was not found.</p>
        </div>
        """

    coupon_id, name, block, flat_number, members, is_used = booking

    if is_used == 1:

        return f"""
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h1 style="color:#F44336;">❌ Already Used</h1>
        <p><b>{name}</b> — Block {block}, Flat {flat_number}</p>
        <p>This coupon has already been redeemed.</p>
        </div>
        """

    mark_coupon_used(coupon_id)

    return f"""
    <div style="font-family:Arial;text-align:center;padding:60px;">
    <h1 style="color:#4CAF50;">✅ Valid Coupon</h1>
    <p style="font-size:20px;"><b>{name}</b></p>
    <p>🏢 Block : {block}</p>
    <p>🏠 Flat : {flat_number}</p>
    <p>👥 Members : {members}</p>
    <p>🎟️ Coupon ID : {coupon_id}</p>
    <p style="color:green;margin-top:20px;">Marked as used ✅</p>
    </div>
    """

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