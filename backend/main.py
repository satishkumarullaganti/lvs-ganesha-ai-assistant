from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.models import ChatRequest
from fastapi.staticfiles import StaticFiles
from backend.validators import validate_flat_number
from backend.chat_service import get_ai_response
from backend.registration_service import registration 
from backend.annaprasada_service import annaprasada_service  
from backend.donation_service import donation_service
from backend.schedule_service import schedule_service
from fastapi.responses import HTMLResponse
from backend.database.database import get_booking_by_coupon, mark_coupon_used
from backend.rag.rag_service import (
    ask_rag,
    is_festival_question
)
from backend.database.database import (
    create_tables,
    get_registrations,
    save_registration,
    save_annaprasada_booking,
    save_cultural_registration,
    get_cultural_registrations
)
import os
import uuid

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

    if not validate_flat_number(data.block, data.flat):

        raise HTTPException(
            status_code=400,
            detail=f"Invalid flat number '{data.flat}' for {data.block} block. Please check and re-enter."
        )

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
# Cultural Programs Register API
# ============================================
# Accepts multipart/form-data since an optional
# audio track file can be uploaded alongside the
# regular text fields.
# ============================================

CULTURAL_TRACKS_DIR = "static/cultural_tracks"
ALLOWED_TRACK_EXTENSIONS = {".mp3", ".m4a"}
MAX_TRACK_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB cap

os.makedirs(CULTURAL_TRACKS_DIR, exist_ok=True)


@app.post("/register-cultural")
async def register_cultural(

    name: str = Form(...),
    block: str = Form(...),
    flat: str = Form(...),
    mobile: str = Form(...),
    categories: str = Form(...),
    other_details: str = Form(""),
    track: UploadFile = File(None)

):

    if not validate_flat_number(block, flat):

        raise HTTPException(
            status_code=400,
            detail=f"Invalid flat number '{flat}' for {block} block. Please check and re-enter."
        )

    if not categories.strip():

        raise HTTPException(
            status_code=400,
            detail="Please select at least one category."
        )

    track_path = None

    # -----------------------------
    # Optional Track Upload
    # -----------------------------
    if track is not None and track.filename:

        file_ext = os.path.splitext(track.filename)[1].lower()

        if file_ext not in ALLOWED_TRACK_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail="Only .mp3 or .m4a files are allowed for the performance track."
            )

        file_bytes = await track.read()

        if len(file_bytes) > MAX_TRACK_SIZE_BYTES:

            raise HTTPException(
                status_code=400,
                detail="Track file is too large. Maximum allowed size is 15 MB."
            )

        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        full_disk_path = os.path.join(CULTURAL_TRACKS_DIR, unique_filename)

        with open(full_disk_path, "wb") as f:
            f.write(file_bytes)

        track_path = f"{CULTURAL_TRACKS_DIR}/{unique_filename}"

    save_cultural_registration(
        name=name,
        block=block,
        flat_number=flat,
        mobile=mobile,
        categories=categories,
        other_details=other_details.strip() if other_details else None,
        track_path=track_path
    )

    return {
        "status": "success",
        "message": f"Cultural Programs registration successful for {name}"
    }


@app.get("/cultural-registrations")
def cultural_registrations():

    rows = get_cultural_registrations()

    result = []

    for row in rows:

        result.append({
            "id": row[0],
            "name": row[1],
            "block": row[2],
            "flat_number": row[3],
            "mobile": row[4],
            "categories": row[5],
            "other_details": row[6],
            "track_path": row[7],
            "created_at": row[8]
        })

    return result

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
    # Only treat this as a booking request if the message
    # doesn't look like a schedule/timing question (e.g.
    # "when is annaprasada" should go to schedule_service,
    # not start the booking flow).
    # ==========================================

    SCHEDULE_QUESTION_HINTS = [
        "when",
        "what time",
        "schedule",
        "timing",
        "day"
    ]

    lower_message_check = message.lower()

    looks_like_schedule_question = any(
        hint in lower_message_check for hint in SCHEDULE_QUESTION_HINTS
    )

    if "annaprasada" in lower_message_check and not looks_like_schedule_question:

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

    # ==========================================
    # Festival Schedule Queries
    # ==========================================
    # Route anything schedule-related to schedule_service
    # so it NEVER reaches Ollama and can't hallucinate.
    # schedule_service.handle_query() already handles:
    # full schedule / today / specific date / day name /
    # event keyword search, with a safe default fallback
    # to the full schedule instead of guessing.
    # ==========================================

    import re

    SCHEDULE_TRIGGER_WORDS = [
        "schedule",
        "schdeule",
        "sched",
        "timing",
        "timings",
        "programme",
        "program",
        "events today",
        "what time",
        "when is",
        "when does",
        "agenda",
        "itinerary",
        "today's events",
        "what's happening",
        "whats happening"
    ]

    lower_message = message.lower()

    # Catches "day 1", "day1", "day 7", etc. for any day number
    # (event now runs a full week, so this covers all days
    # without needing to list each one individually)
    day_number_pattern = re.search(r"\bday\s?\d+\b", lower_message)

    if any(word in lower_message for word in SCHEDULE_TRIGGER_WORDS) or day_number_pattern:

        return {
            "response": schedule_service.handle_query(message)
        }

    # -----------------------------
    # Festival Knowledge / RAG
    # -----------------------------

    if is_festival_question(message):

        try:

            rag_result = ask_rag(message)

            return {
                "response": rag_result.get("response", ""),
                "sources": rag_result.get("sources", [])
            }

        except Exception as e:

            print(f"RAG error: {e}")

            return {
                "response": (
                    "Sorry, I am unable to access "
                    "the festival information right now."
                )
            }

    # -----------------------------
    # General AI Chat
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