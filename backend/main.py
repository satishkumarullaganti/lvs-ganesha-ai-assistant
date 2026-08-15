from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File, Response
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
from fastapi.responses import HTMLResponse, JSONResponse
from backend.database.database import get_booking_by_coupon, serve_annaprasada_members
from dotenv import load_dotenv
load_dotenv()
from backend.admin.admin_routes import router as admin_router, require_admin
from backend.announcement_service import (
    get_active_announcements,
    get_all_announcements,
    add_announcement,
    deactivate_announcement
)
from backend.push_service import (
    save_subscription,
    remove_subscription,
    send_push_to_all
)
from backend.config import VAPID_PUBLIC_KEY
from backend.rag.rag_service import (
    ask_rag,
    is_festival_question
)
from backend.database.database import (
    create_tables,
    get_registrations,
    save_registration,
    check_duplicate_competition_registration,
    save_annaprasada_booking,
    save_cultural_registration,
    get_cultural_registrations,
    check_recent_duplicate_cultural_registration,
    save_volunteer_registration,
    get_registered_tasks_for_person,
    get_volunteer_registrations
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
app.include_router(admin_router)

# ============================================
# Per-Visitor Session Handling
# ============================================
# Every visitor gets a private session_id stored
# in a cookie, so their registration/annaprasada/
# donation/chat state is independent from every
# other visitor. Without this, all visitors share
# one global state and can hijack each other's
# conversation flows.
# ============================================

SESSION_COOKIE_NAME = "lvs_session_id"


def get_or_create_session_id(request: Request, response: Response) -> str:

    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_id:
        session_id = str(uuid.uuid4())

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=60 * 60 * 24 * 7,  # 7 days
        httponly=True,
        samesite="lax"
    )

    return session_id


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

    # --------------------------------------------
    # Duplicate competition-entry check
    # --------------------------------------------
    # Unlike cultural programs, a competition only has one
    # entry per person - registering for the same
    # competition twice is always a genuine duplicate.
    # --------------------------------------------

    if check_duplicate_competition_registration(
        name=data.name,
        block=data.block,
        flat_number=data.flat,
        competition=data.competition
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                f"You've already registered for {data.competition}. "
                "If this is a mistake, please contact a volunteer."
            )
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

    cleaned_other_details = other_details.strip() if other_details else None

    # --------------------------------------------
    # Accidental double-submit guard
    # --------------------------------------------
    # A participant CAN register for the same category
    # more than once (different performances). This only
    # blocks the exact same name + category set + details
    # being submitted again within a few minutes - almost
    # certainly a double-click or resubmission, not a
    # genuine second performance.
    # --------------------------------------------

    if check_recent_duplicate_cultural_registration(
        name=name,
        categories=categories,
        other_details=cleaned_other_details
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "This looks like it was already submitted a moment ago "
                "(same name, category, and details). If this is actually "
                "a different performance, please add a distinguishing "
                "note, or wait a few minutes and try again."
            )
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
        other_details=cleaned_other_details,
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
# Volunteer Registration Model
# ============================================

class VolunteerRequest(BaseModel):
    name: str
    block: str
    flat: str
    mobile: str
    tasks: str
    other_details: str = ""

# ============================================
# Volunteer Register API
# ============================================

@app.post("/register-volunteer")
def register_volunteer(data: VolunteerRequest):

    if not validate_flat_number(data.block, data.flat):

        raise HTTPException(
            status_code=400,
            detail=f"Invalid flat number '{data.flat}' for {data.block} block. Please check and re-enter."
        )

    if not data.tasks.strip():

        raise HTTPException(
            status_code=400,
            detail="Please select at least one task to volunteer for."
        )

    # --------------------------------------------
    # Duplicate volunteer-task check
    # --------------------------------------------
    # A volunteer task (e.g. "Registration Desk") has no
    # equivalent of "two different performances" - there's
    # no legitimate reason to sign up for the exact same
    # task twice. Different, not-yet-registered tasks are
    # still allowed through.
    # --------------------------------------------

    requested_tasks = [
        t.strip() for t in data.tasks.split(",") if t.strip()
    ]

    already_registered_tasks = get_registered_tasks_for_person(
        name=data.name,
        block=data.block,
        flat_number=data.flat
    )

    duplicate_tasks = [
        t for t in requested_tasks
        if t.lower() in already_registered_tasks
    ]

    if duplicate_tasks:

        duplicate_list = ", ".join(duplicate_tasks)

        raise HTTPException(
            status_code=400,
            detail=(
                f"You're already signed up for: {duplicate_list}. "
                "Please remove already-registered tasks, or choose "
                "different ones."
            )
        )

    save_volunteer_registration(
        name=data.name,
        block=data.block,
        flat_number=data.flat,
        mobile=data.mobile,
        tasks=data.tasks,
        other_details=data.other_details.strip() if data.other_details else None
    )

    return {
        "status": "success",
        "message": f"Thank you {data.name}! Your volunteer registration is confirmed."
    }


@app.get("/volunteer-registrations")
def volunteer_registrations():

    rows = get_volunteer_registrations()

    result = []

    for row in rows:

        result.append({
            "id": row[0],
            "name": row[1],
            "block": row[2],
            "flat_number": row[3],
            "mobile": row[4],
            "tasks": row[5],
            "other_details": row[6],
            "created_at": row[7]
        })

    return result
# ============================================
# Start Fresh Chat Registration
# ============================================

@app.post("/register-chat")
def register_chat(request: Request, response: Response):

    # Always start a fresh registration session
    # for THIS visitor only (session-scoped).
    session_id = get_or_create_session_id(request, response)

    return {
        "response": registration.start(session_id)
    }
# ============================================
# Chat API
# ============================================

@app.post("/chat")
def chat(chat_request: ChatRequest, request: Request, response: Response):

    session_id = get_or_create_session_id(request, response)

    message = chat_request.message.strip()

    # ==========================================
    # Helper: append the cancel hint to a flow's
    # response, but only while that flow is still
    # active (a flow's final "thank you"/receipt
    # message means it just finished, so there's
    # nothing left to cancel).
    # ==========================================

    def _with_cancel_hint(reply_text, still_active):

        if not still_active:
            return reply_text

        if "cancel" in reply_text.lower():
            return reply_text

        return reply_text + "\n\n(Type 'cancel' anytime to stop.)"

    # ==========================================
    # Universal Cancel / Exit
    # ==========================================
    # Checked BEFORE any flow's is_active() check, so a
    # resident can always back out of a stuck or abandoned
    # donation/registration/Annaprasada flow, regardless of
    # which one they're currently in. Without this, a
    # half-finished flow silently swallows every later
    # message (e.g. a schedule question gets treated as a
    # "Full Name" answer) until the session naturally resets.
    # ==========================================

    CANCEL_WORDS = {
        "cancel", "exit", "stop", "quit",
        "start over", "cancel registration",
        "reset", "never mind", "nevermind"
    }

    if message.strip().lower() in CANCEL_WORDS:

        was_active = (
            donation_service.is_active(session_id)
            or registration.is_active(session_id)
            or annaprasada_service.is_active(session_id)
        )

        donation_service.cancel(session_id)
        registration.cancel(session_id)
        annaprasada_service.cancel(session_id)

        if was_active:

            return {
                "response": (
                    "❌ Okay, I've cancelled that for you.\n\n"
                    "How else can I help - schedule, donation, "
                    "registration, or something else?"
                )
            }

        return {
            "response": "There's nothing active to cancel right now. How can I help?"
        }

    # ==========================================
    # Continue Donation Flow (if active)
    # ==========================================

    if donation_service.is_active(session_id):

        reply = donation_service.process_donation(session_id, message)

        return {
            "response": _with_cancel_hint(
                reply,
                donation_service.is_active(session_id)
            )
        }

    # ==========================================
    # Start Donation Flow
    # ==========================================
    # Only treat this as a request to START donating if the
    # message doesn't look like an informational question
    # (e.g. "is there a minimum donation amount" or "who
    # sponsored the idol" should be answered by RAG, not
    # dropped into the donation transaction flow).
    # ==========================================

    DONATION_QUESTION_HINTS = [
        "is there",
        "what is",
        "what are",
        "how much",
        "minimum",
        "maximum",
        "who",
        "why",
        "when",
        "amount",
        "?"
    ]

    lower_message_donation_check = message.lower()

    looks_like_donation_question = any(
        hint in lower_message_donation_check
        for hint in DONATION_QUESTION_HINTS
    )

    if "donation" in lower_message_donation_check and not looks_like_donation_question:

        return {
            "response": donation_service.start_donation(session_id)
        }

    # ==========================================
    # Continue Annaprasada Booking (if active)
    # ==========================================

    if annaprasada_service.is_active(session_id):

        reply = annaprasada_service.process_booking(session_id, message)

        return {
            "response": _with_cancel_hint(
                reply,
                annaprasada_service.is_active(session_id)
            )
        }

    # ==========================================
    # Start Annaprasada Coupon Booking
    # ==========================================
    # Only treat this as a booking request if the message
    # doesn't look like a schedule/timing question (e.g.
    # "when is annaprasada" should go to schedule_service,
    # not start the booking flow).
    # ==========================================

    # ==========================================
    # Start Annaprasada Coupon Booking
    # ==========================================
    # Only treat this as a booking-status check if the
    # message doesn't look like an informational question
    # (e.g. "when is annaprasada" -> schedule_service,
    # "how do I redeem my Annaprasada QR coupon" -> RAG,
    # not a booking-status lookup).
    # ==========================================

    INFORMATIONAL_QUESTION_HINTS = [
        "when", "what time", "schedule", "timing", "day",
        "how", "what is", "what are", "is there", "does",
        "why", "who", "?"
    ]

    lower_message_check = message.lower()

    looks_like_schedule_question = any(
        hint in lower_message_check for hint in INFORMATIONAL_QUESTION_HINTS
    )

    if "annaprasada" in lower_message_check and not looks_like_schedule_question:

        result = annaprasada_service.check_booking_status(session_id)

        return {
            "response": result["response"]
        }

    # -----------------------------
    # Start / Restart Registration
    # -----------------------------
    if message.lower().strip() == "register":
        # Always start a fresh registration session

        return {
            "response": registration.start(session_id)
        }

    # -----------------------------
    # Continue Registration
    # -----------------------------
    if registration.is_active(session_id):

        reply = registration.process(session_id, message)

        return {
            "response": _with_cancel_hint(
                reply,
                registration.is_active(session_id)
            )
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
        "whats happening",
        "location",
        "venue",
        "where is",
        "where does",
        "where will",
        "address",
        "party hall"
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

    reply = get_ai_response(session_id, message)

    return {
        "response": reply
    }

# ============================================
# Donation Payment Proof Upload (Screenshot)
# ============================================
# Accepts multipart/form-data since a screenshot
# image is uploaded, mirroring the Cultural
# Programs track-upload pattern above.
# ============================================

DONATION_PROOFS_DIR = "static/donation_proofs"
ALLOWED_PROOF_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_PROOF_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB cap

os.makedirs(DONATION_PROOFS_DIR, exist_ok=True)


@app.post("/donation/upload-proof")
async def donation_upload_proof(
    request: Request,
    response: Response,
    proof: UploadFile = File(...)
):

    session_id = get_or_create_session_id(request, response)

    if not donation_service.is_active(session_id):

        raise HTTPException(
            status_code=400,
            detail="No donation in progress for this session."
        )

    file_ext = os.path.splitext(proof.filename)[1].lower()

    if file_ext not in ALLOWED_PROOF_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Only JPG or PNG screenshots are allowed."
        )

    file_bytes = await proof.read()

    if len(file_bytes) > MAX_PROOF_SIZE_BYTES:

        raise HTTPException(
            status_code=400,
            detail="Screenshot is too large. Maximum allowed size is 8 MB."
        )

    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    full_disk_path = os.path.join(DONATION_PROOFS_DIR, unique_filename)

    with open(full_disk_path, "wb") as f:
        f.write(file_bytes)

    proof_path = f"{DONATION_PROOFS_DIR}/{unique_filename}"

    result = donation_service.finalize_with_screenshot(session_id, proof_path)

    if result is None:

        raise HTTPException(
            status_code=400,
            detail="Unable to process this donation right now. Please try again."
        )

    return {
        "response": result
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

    coupon_id, name, block, flat_number, members, is_used, served_count = booking

    total_members = int(members)
    served_count = served_count or 0
    remaining = total_members - served_count

    if remaining <= 0:

        return f"""
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h1 style="color:#F44336;">❌ Fully Redeemed</h1>
        <p><b>{name}</b> — Block {block}, Flat {flat_number}</p>
        <p>All {total_members} member(s) on this coupon have already been served.</p>
        </div>
        """

    already_served_note = (
        f"<p style='color:#888;'>Already served: {served_count} of {total_members}</p>"
        if served_count > 0 else ""
    )

    return f"""
    <div style="font-family:Arial;text-align:center;padding:60px;">
    <h1 style="color:#4CAF50;">✅ Valid Coupon</h1>
    <p style="font-size:20px;"><b>{name}</b></p>
    <p>🏢 Block : {block}</p>
    <p>🏠 Flat : {flat_number}</p>
    <p>👥 Total Members : {total_members}</p>
    {already_served_note}
    <p style="font-size:18px;color:#ff9800;"><b>Remaining : {remaining}</b></p>
    <p>🎟️ Coupon ID : {coupon_id}</p>

    <form method="post" action="/verify/{coupon_id}/serve" style="margin-top:24px;">
        <label for="serve_count">How many are being served now?</label><br><br>
        <input
            type="number"
            id="serve_count"
            name="serve_count"
            min="1"
            max="{remaining}"
            value="{remaining}"
            style="font-size:18px;padding:8px;width:80px;text-align:center;border-radius:8px;border:1px solid #ccc;">
        <br><br>
        <button
            type="submit"
            style="background:#4CAF50;color:white;border:none;border-radius:10px;padding:12px 28px;font-size:16px;cursor:pointer;">
            ✅ Confirm & Serve
        </button>
    </form>

    </div>
    """


@app.post("/verify/{coupon_id}/serve", response_class=HTMLResponse)
def serve_coupon(coupon_id: str, request: Request, serve_count: int = Form(...)):

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

    if serve_count < 1:

        return """
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h1 style="color:#F44336;">⚠️ Invalid Count</h1>
        <p>Please enter at least 1.</p>
        </div>
        """

    result = serve_annaprasada_members(coupon_id, serve_count)

    if result is None:

        return """
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h1 style="color:#F44336;">⚠️ Invalid Coupon</h1>
        <p>This coupon ID was not found.</p>
        </div>
        """

    if result["remaining"] <= 0:

        status_line = "<p style='color:green;font-size:18px;'>✅ Fully redeemed - nothing left on this coupon.</p>"

    else:

        status_line = (
            f"<p style='color:#ff9800;font-size:18px;'>"
            f"{result['remaining']} member(s) still remaining on this coupon. "
            f"Scan again when they arrive.</p>"
        )

    return f"""
    <div style="font-family:Arial;text-align:center;padding:60px;">
    <h1 style="color:#4CAF50;">✅ Served {result['served_now']}</h1>
    <p>🎟️ Coupon ID : {coupon_id}</p>
    <p>Total served so far : {result['new_served_count']} of {result['total_members']}</p>
    {status_line}
    </div>
    """


# ============================================
# Continuous Volunteer Scanner (JSON API + page)
# ============================================
# The /verify/{coupon_id} page above works fine for a
# single scan, but it fully navigates the browser away
# from the camera each time - meaning a volunteer has to
# close and reopen their camera app for every single
# person. These two JSON endpoints let a JS-based
# in-browser scanner (below) check and redeem coupons
# via background fetch() calls instead, so the camera
# view never has to close between scans.
# ============================================

@app.get("/api/coupon-status/{coupon_id}")
def api_coupon_status(coupon_id: str, request: Request):

    if request.cookies.get(VOLUNTEER_COOKIE_NAME) != VOLUNTEER_COOKIE_VALUE:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    booking = get_booking_by_coupon(coupon_id)

    if not booking:
        return JSONResponse({"error": "invalid_coupon"}, status_code=404)

    coupon_id, name, block, flat_number, members, is_used, served_count = booking

    total_members = int(members)
    served_count = served_count or 0
    remaining = total_members - served_count

    return {
        "coupon_id": coupon_id,
        "name": name,
        "block": block,
        "flat_number": flat_number,
        "total_members": total_members,
        "served_count": served_count,
        "remaining": remaining
    }


@app.post("/api/coupon-serve/{coupon_id}")
async def api_coupon_serve(coupon_id: str, request: Request):

    if request.cookies.get(VOLUNTEER_COOKIE_NAME) != VOLUNTEER_COOKIE_VALUE:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        body = await request.json()
        serve_count = int(body.get("serve_count", 0))
    except (ValueError, TypeError):
        return JSONResponse({"error": "invalid_count"}, status_code=400)

    if serve_count < 1:
        return JSONResponse({"error": "invalid_count"}, status_code=400)

    result = serve_annaprasada_members(coupon_id, serve_count)

    if result is None:
        return JSONResponse({"error": "invalid_coupon"}, status_code=404)

    return result


@app.get("/volunteer-scan", response_class=HTMLResponse)
def volunteer_scan(request: Request):

    if request.cookies.get(VOLUNTEER_COOKIE_NAME) != VOLUNTEER_COOKIE_VALUE:

        return """
        <div style="font-family:Arial;text-align:center;padding:60px;">
        <h2 style="color:#F44336;">🔒 Volunteer Access Required</h2>
        <p>This page is for volunteer use only during coupon distribution.</p>
        <p><a href="/volunteer-login">Enter volunteer PIN</a></p>
        </div>
        """

    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Volunteer Scanner - LVS Ganesha Festival</title>
<script src="https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
<style>
    * { box-sizing: border-box; }
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #111;
        color: #fff;
        overflow: hidden;
    }
    #header {
        background: #ff9800;
        text-align: center;
        padding: 12px;
        font-weight: bold;
        font-size: 18px;
    }
    #qr-reader {
        width: 100%;
        max-width: 500px;
        margin: 0 auto;
    }
    #status-message {
        text-align: center;
        padding: 16px;
        font-size: 15px;
        color: #ccc;
    }
    #overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.85);
        z-index: 999;
        align-items: center;
        justify-content: center;
    }
    #overlay-card {
        background: #fff;
        color: #222;
        border-radius: 16px;
        padding: 28px 24px;
        width: 90%;
        max-width: 380px;
        text-align: center;
    }
    #overlay-card h2 {
        margin-top: 0;
    }
    #overlay-card input[type="number"] {
        font-size: 22px;
        padding: 10px;
        width: 90px;
        text-align: center;
        border-radius: 8px;
        border: 1px solid #ccc;
        margin: 14px 0;
    }
    .btn {
        display: inline-block;
        border: none;
        border-radius: 10px;
        padding: 12px 26px;
        font-size: 16px;
        cursor: pointer;
        margin: 6px;
    }
    .btn-confirm {
        background: #4CAF50;
        color: white;
    }
    .btn-dismiss {
        background: #999;
        color: white;
    }
    .error-text {
        color: #F44336;
        font-weight: bold;
    }
    .success-text {
        color: #4CAF50;
        font-weight: bold;
    }
    .warn-text {
        color: #ff9800;
        font-weight: bold;
    }
</style>
</head>
<body>

<div id="header">🍛 Volunteer Coupon Scanner</div>
<div id="qr-reader"></div>
<div id="status-message">Point the camera at a resident's QR code</div>

<div id="overlay">
    <div id="overlay-card"></div>
</div>

<script>
const statusMessage = document.getElementById("status-message");
const overlay = document.getElementById("overlay");
const overlayCard = document.getElementById("overlay-card");

let isBusy = false;
let scanner = null;

function extractCouponId(decodedText) {
    // The QR encodes a full /verify/{coupon_id} URL - just
    // take the final path segment as the coupon ID.
    const parts = decodedText.split("/").filter(Boolean);
    return parts[parts.length - 1];
}

function showOverlay(html) {
    overlayCard.innerHTML = html;
    overlay.style.display = "flex";
}

function hideOverlayAndResume() {
    overlay.style.display = "none";
    isBusy = false;
    statusMessage.textContent = "Point the camera at a resident's QR code";
    if (scanner) {
        scanner.resume();
    }
}

function fetchStatus(couponId) {

    fetch("/api/coupon-status/" + encodeURIComponent(couponId))
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {

            if (!result.ok) {

                const message = result.data.error === "invalid_coupon"
                    ? "This coupon was not found."
                    : "Session expired - please re-enter the volunteer PIN.";

                showOverlay(
                    '<h2 class="error-text">⚠️ Error</h2>' +
                    '<p>' + message + '</p>' +
                    '<button class="btn btn-dismiss" onclick="hideOverlayAndResume()">OK</button>'
                );
                return;
            }

            const data = result.data;

            if (data.remaining <= 0) {

                showOverlay(
                    '<h2 class="error-text">❌ Fully Redeemed</h2>' +
                    '<p><b>' + data.name + '</b></p>' +
                    '<p>Block ' + data.block + ', Flat ' + data.flat_number + '</p>' +
                    '<p>All ' + data.total_members + ' member(s) already served.</p>' +
                    '<button class="btn btn-dismiss" onclick="hideOverlayAndResume()">OK</button>'
                );
                return;
            }

            const alreadyServedNote = data.served_count > 0
                ? '<p style="color:#888;">Already served: ' + data.served_count + ' of ' + data.total_members + '</p>'
                : '';

            showOverlay(
                '<h2 class="success-text">✅ Valid Coupon</h2>' +
                '<p><b>' + data.name + '</b></p>' +
                '<p>Block ' + data.block + ', Flat ' + data.flat_number + '</p>' +
                '<p>Total Members: ' + data.total_members + '</p>' +
                alreadyServedNote +
                '<p class="warn-text">Remaining: ' + data.remaining + '</p>' +
                '<label>How many are being served now?</label><br>' +
                '<input type="number" id="serve-count-input" min="1" max="' + data.remaining + '" value="' + data.remaining + '"><br>' +
                '<button class="btn btn-confirm" onclick="confirmServe(\\'' + data.coupon_id + '\\')">✅ Confirm & Serve</button>' +
                '<br><button class="btn btn-dismiss" onclick="hideOverlayAndResume()">Cancel</button>'
            );
        })
        .catch(function () {
            showOverlay(
                '<h2 class="error-text">⚠️ Network Error</h2>' +
                '<p>Could not reach the server. Check your connection and try again.</p>' +
                '<button class="btn btn-dismiss" onclick="hideOverlayAndResume()">OK</button>'
            );
        });
}

function confirmServe(couponId) {

    const input = document.getElementById("serve-count-input");
    const serveCount = parseInt(input.value, 10);

    if (!serveCount || serveCount < 1) {
        return;
    }

    fetch("/api/coupon-serve/" + encodeURIComponent(couponId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ serve_count: serveCount })
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {

            if (!result.ok) {
                showOverlay(
                    '<h2 class="error-text">⚠️ Error</h2>' +
                    '<p>Could not update this coupon. Please try again.</p>' +
                    '<button class="btn btn-dismiss" onclick="hideOverlayAndResume()">OK</button>'
                );
                return;
            }

            const data = result.data;

            const statusLine = data.remaining <= 0
                ? '<p class="success-text">✅ Fully redeemed - nothing left on this coupon.</p>'
                : '<p class="warn-text">' + data.remaining + ' member(s) still remaining. Scan again when they arrive.</p>';

            showOverlay(
                '<h2 class="success-text">✅ Served ' + data.served_now + '</h2>' +
                '<p>Total served so far: ' + data.new_served_count + ' of ' + data.total_members + '</p>' +
                statusLine +
                '<button class="btn btn-confirm" onclick="hideOverlayAndResume()">Next</button>'
            );

            // Auto-resume scanning shortly after a successful serve
            setTimeout(hideOverlayAndResume, 2500);
        })
        .catch(function () {
            showOverlay(
                '<h2 class="error-text">⚠️ Network Error</h2>' +
                '<p>Could not reach the server. Please try again.</p>' +
                '<button class="btn btn-dismiss" onclick="hideOverlayAndResume()">OK</button>'
            );
        });
}

function onScanSuccess(decodedText) {

    if (isBusy) return;
    isBusy = true;

    statusMessage.textContent = "Checking coupon...";

    if (scanner) {
        scanner.pause(true);
    }

    const couponId = extractCouponId(decodedText);
    fetchStatus(couponId);
}

document.addEventListener("DOMContentLoaded", function () {

    scanner = new Html5Qrcode("qr-reader");

    scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        onScanSuccess
    ).catch(function (err) {
        statusMessage.textContent = "Camera access failed - please allow camera permission and reload.";
    });

});
</script>

</body>
</html>
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
# Dynamic Announcements
# ============================================
# Announcements are stored in a plain JSON file and read
# fresh on every request (see announcement_service.py) -
# adding/removing one takes effect immediately, with no
# server restart or redeployment needed.
# ============================================

@app.get("/api/announcements")
def api_get_announcements():
    """
    Public endpoint - the frontend polls this periodically
    to display active announcements, even without push
    notifications enabled.
    """
    return {"announcements": get_active_announcements()}


class AnnouncementRequest(BaseModel):
    message: str
    type: str = "info"


@app.post("/admin/announcements")
def admin_add_announcement(data: AnnouncementRequest, request: Request):

    require_admin(request)

    if not data.message.strip():
        raise HTTPException(status_code=400, detail="Announcement message cannot be empty.")

    new_announcement = add_announcement(data.message, data.type)

    # Push it to every subscribed device immediately
    push_result = send_push_to_all(
        title="LVS Ganesha Festival",
        body=data.message
    )

    return {
        "announcement": new_announcement,
        "push": push_result
    }


@app.get("/admin/announcements")
def admin_list_announcements(request: Request):

    require_admin(request)

    return {"announcements": get_all_announcements()}


@app.delete("/admin/announcements/{announcement_id}")
def admin_delete_announcement(announcement_id: str, request: Request):

    require_admin(request)

    found = deactivate_announcement(announcement_id)

    if not found:
        raise HTTPException(status_code=404, detail="Announcement not found.")

    return {"status": "deactivated", "id": announcement_id}


# ============================================
# Web Push Subscriptions
# ============================================

@app.get("/api/vapid-public-key")
def api_vapid_public_key():
    """
    Public endpoint - the frontend fetches this before
    subscribing to push notifications, so the VAPID public
    key doesn't need to be hardcoded in the JS.
    """
    return {"public_key": VAPID_PUBLIC_KEY}


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict


@app.post("/api/push-subscribe")
def api_push_subscribe(data: PushSubscriptionRequest):

    result = save_subscription({
        "endpoint": data.endpoint,
        "keys": data.keys
    })

    return result


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


@app.post("/api/push-unsubscribe")
def api_push_unsubscribe(data: PushUnsubscribeRequest):

    remove_subscription(data.endpoint)

    return {"status": "removed"}

# ============================================
# Serve Frontend (must be LAST - catches all
# remaining routes and serves frontend/index.html
# for "/" and other static files under frontend/)
# ============================================

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


