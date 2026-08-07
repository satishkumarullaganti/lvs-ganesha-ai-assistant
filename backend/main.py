from fastapi import FastAPI, Request, Form
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Volunteer Access Settings
# ============================================

VOLUNTEER_PIN = "2026"
VOLUNTEER_COOKIE_NAME = "lvs_volunteer_access"
VOLUNTEER_COOKIE_VALUE = "granted"

# ============================================
# Home (API info - moved from "/" to "/api")
# ============================================

@app.get("/api")
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
# Volunteer Login (PIN gate)
# ============================================

@app.get("/volunteer-login", response_class=HTMLResponse)
def volunteer_login_page():

    return """
    <div style="font-family:Arial;max-width:340px;margin:60px auto;padding:30px;
                border:1px solid #ddd;border-radius:10px;text-align:center;">
        <h2>🙏 Volunteer Access</h2>
        <p>Enter today's PIN to unlock coupon scanning on this phone.</p>
        <form method="post" action="/volunteer-login">
            <input type="password" name="pin" placeholder="Enter PIN"
                   style="padding:10px;width:80%;font-size:16px;margin-bottom:15px;
                          border:1px solid #ccc;border-radius:6px;" required>
            <br>
            <button type="submit"
                    style="padding:10px 25px;font-size:16px;background:#4CAF50;
                           color:white;border:none;border-radius:6px;cursor:pointer;">
                Unlock
            </button>
        </form>
    </div>
    """

@app.post("/volunteer-login", response_class=HTMLResponse)
def volunteer_login_submit(request: Request, pin: str = Form(...)):

    from fastapi.responses import RedirectResponse

    if pin.strip() != VOLUNTEER_PIN:

        return """
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h2 style="color:#F44336;">❌ Incorrect PIN</h2>
        <p><a href="/volunteer-login">Try again</a></p>
        </div>
        """

    response = HTMLResponse("""
    <div style="font-family:Arial;text-align:center;padding:60px;">
    <h2 style="color:#4CAF50;">✅ Access Granted</h2>
    <p>This phone can now scan and verify Annaprasada coupons.</p>
    <p>You can close this page and start scanning QR codes.</p>
    </div>
    """)

    response.set_cookie(
        key=VOLUNTEER_COOKIE_NAME,
        value=VOLUNTEER_COOKIE_VALUE,
        max_age=60 * 60 * 24,  # 24 hours - plenty for a one-day event
        httponly=True,
        samesite="lax"
    )

    return response

# ============================================
# Verify Annaprasada Coupon (Volunteer Scan)
# ============================================

@app.get("/verify/{coupon_id}", response_class=HTMLResponse)
def verify_coupon(coupon_id: str, request: Request):

    # -----------------------------
    # Volunteer access check
    # -----------------------------
    if request.cookies.get(VOLUNTEER_COOKIE_NAME) != VOLUNTEER_COOKIE_VALUE:

        return """
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h2 style="color:#F44336;">🔒 Volunteer Access Required</h2>
        <p>This page is for volunteer use only during coupon distribution.</p>
        <p><a href="/volunteer-login">Enter volunteer PIN</a></p>
        </div>
        """

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

# ============================================
# Serve Frontend (must be LAST - catches all
# remaining routes and serves frontend/index.html
# for "/" and other static files under frontend/)
# ============================================

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")