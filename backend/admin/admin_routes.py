import os
import secrets
import hmac
import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    UploadFile,
    File
)

from fastapi.responses import (
    StreamingResponse
)

from pydantic import BaseModel

from io import BytesIO

from backend.admin.admin_service import (
    get_dashboard_summary,
    get_table_data,
    get_record_by_id,
    update_record,
    delete_record,
    create_excel_file
)

from backend.database.database import (
    verify_admin_password,
    get_admin_user_by_username,
    log_admin_activity,
    get_recent_activity_log,
    change_admin_password,
    add_admin_user,
    get_all_admin_users,
    delete_admin_user,
    save_cultural_registration,
    save_annaprasada_booking
)

from backend.register_ocr_service import (
    extract_register_rows,
    extract_cultural_signup_rows,
    extract_annaprasada_rows
)
from backend.validators import validate_flat_number
from backend.donation_service import donation_service
from backend.annaprasada_service import generate_coupon_id
from backend.coupon_image_service import generate_annaprasada_coupon
from backend.whatsapp_service import send_annaprasada_confirmation
from backend.config import PUBLIC_BASE_URL

# ============================================
# Admin Router
# ============================================

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# ============================================
# Admin Credentials
# ============================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    ""
)


# ============================================
# Active Admin Sessions
# ============================================
# Maps session_token -> username, so every action can be
# attributed to a specific person, not just "an admin".

admin_sessions = {}


# ============================================
# Active Admin Session -> Section Mapping
# ============================================
# None/empty = full admin (sees every section, can
# edit). A value here restricts that session to VIEW
# only the matching section, for its whole lifetime.

admin_session_sections = {}


# ============================================
# Get Current Admin Username
# ============================================

def get_current_admin_username(request: Request):

    session_token = request.cookies.get("admin_session")

    return admin_sessions.get(session_token, "unknown")


# ============================================
# Get Current Admin's Assigned Section
# ============================================
# None means this session is a full admin (no
# restriction). A string means it can only view that
# one section.

def get_current_admin_section(request: Request):

    session_token = request.cookies.get("admin_session")

    return admin_session_sections.get(session_token)


# ============================================
# Login Request
# ============================================

class AdminLoginRequest(BaseModel):

    username: str
    password: str


class ChangePasswordRequest(BaseModel):

    old_password: str
    new_password: str


# ============================================
# Verify Admin Session
# ============================================

def require_admin(request: Request):

    session_token = request.cookies.get(
        "admin_session"
    )

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Admin login required"
        )

    if session_token not in admin_sessions:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin session"
        )

    return True


# ============================================
# Verify Section-Restricted View Access
# ============================================
# Used on every GET route that only shows ONE section's
# data. A full admin (no section on their account) can
# view every section, same as before this feature
# existed. A section-restricted account is only let
# through when the section it's assigned matches the
# section being requested.

def require_section_view(request: Request, section: str):

    require_admin(request)

    account_section = get_current_admin_section(request)

    if account_section and account_section != section:
        raise HTTPException(
            status_code=403,
            detail="Your login does not have access to this section."
        )


# ============================================
# Verify FULL (non-restricted) Admin Access
# ============================================
# Used on anything that changes data, spans multiple
# sections (e.g. the dashboard, the activity log), or
# manages other admin accounts. A section-restricted
# login is always view-only and is blocked here,
# regardless of which section it's assigned to.

def require_full_admin(request: Request):

    require_admin(request)

    if get_current_admin_section(request):
        raise HTTPException(
            status_code=403,
            detail="Your login is view-only and cannot perform this action."
        )


# ============================================
# Admin Login
# ============================================

@router.post("/login")
def admin_login(
    credentials: AdminLoginRequest
):

    # --------------------------------------------
    # First, check individual admin accounts (the
    # proper multi-user system) - each person has
    # their own username/password, and every action
    # gets attributed to them specifically.
    # --------------------------------------------

    if verify_admin_password(credentials.username, credentials.password):

        user_row = get_admin_user_by_username(credentials.username)
        logged_in_username = user_row[1]  # stored username, correct casing
        logged_in_section = user_row[4]   # None = full admin

    # --------------------------------------------
    # Fall back to the original single shared .env
    # credential, so nothing breaks for whoever was
    # already using it before individual accounts
    # existed.
    # --------------------------------------------

    elif (
        ADMIN_PASSWORD
        and hmac.compare_digest(credentials.username, ADMIN_USERNAME)
        and hmac.compare_digest(credentials.password, ADMIN_PASSWORD)
    ):

        logged_in_username = ADMIN_USERNAME
        logged_in_section = None  # the .env fallback account is always full admin

    else:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    session_token = secrets.token_urlsafe(
        32
    )

    admin_sessions[session_token] = logged_in_username
    admin_session_sections[session_token] = logged_in_section

    log_admin_activity(logged_in_username, "logged_in")

    response = {
        "success": True,
        "message": "Admin login successful"
    }

    from fastapi.responses import JSONResponse

    result = JSONResponse(
        content=response
    )

    result.set_cookie(
        key="admin_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return result


# ============================================
# Admin Logout
# ============================================

@router.post("/logout")
def admin_logout(
    request: Request
):

    session_token = request.cookies.get(
        "admin_session"
    )

    if session_token:

        logged_out_username = admin_sessions.get(session_token, "unknown")

        admin_sessions.pop(
            session_token,
            None
        )

        admin_session_sections.pop(
            session_token,
            None
        )

        log_admin_activity(logged_out_username, "logged_out")

    from fastapi.responses import JSONResponse

    result = JSONResponse(
        content={
            "success": True,
            "message": "Logged out successfully"
        }
    )

    result.delete_cookie(
        "admin_session"
    )

    return result


# ============================================
# Change Own Password
# ============================================
# Lets any logged-in individual admin (not the single
# shared .env fallback account) update their own password
# without needing server access. Requires the current
# password to be re-entered as confirmation.
# ============================================

@router.post("/change-password")
def admin_change_password(
    request: Request,
    body: ChangePasswordRequest
):

    require_admin(request)

    current_username = get_current_admin_username(request)

    # The single shared .env-based fallback account has no
    # row in admin_users, so there's nothing to update for it.
    if current_username == ADMIN_USERNAME:

        raise HTTPException(
            status_code=400,
            detail="This account's password is set in the server's "
                   "environment file and can't be changed here. "
                   "Please contact whoever manages the server."
        )

    if len(body.new_password) < 8:

        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters long."
        )

    if not verify_admin_password(current_username, body.old_password):

        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect."
        )

    change_admin_password(current_username, body.new_password)

    log_admin_activity(current_username, "changed_own_password")

    return {
        "success": True,
        "message": "Password updated successfully."
    }


# ============================================
# Check Login Status
# ============================================

@router.get("/auth/status")
def auth_status(
    request: Request
):

    session_token = request.cookies.get(
        "admin_session"
    )

    authenticated = (
        session_token in admin_sessions
        if session_token
        else False
    )

    return {
        "authenticated": authenticated,
        "username": admin_sessions.get(session_token) if authenticated else None,
        "section": admin_session_sections.get(session_token) if authenticated else None
    }


# ============================================
# Dashboard Summary
# ============================================

@router.get("/dashboard")
def dashboard(
    request: Request
):

    require_full_admin(request)

    return get_dashboard_summary()


# ============================================
# Registrations
# ============================================

@router.get("/registrations")
def registrations(
    request: Request
):

    require_section_view(request, "registrations")

    columns, rows = get_table_data(
        "registrations"
    )

    return {
        "columns": columns,
        "data": rows
    }


# ============================================
# Cultural Registrations
# ============================================

@router.get("/cultural")
def cultural(
    request: Request
):

    require_section_view(request, "cultural")

    columns, rows = get_table_data(
        "cultural"
    )

    return {
        "columns": columns,
        "data": rows
    }


# ============================================
# Volunteers
# ============================================

@router.get("/volunteers")
def volunteers(
    request: Request
):

    require_section_view(request, "volunteers")

    columns, rows = get_table_data(
        "volunteers"
    )

    return {
        "columns": columns,
        "data": rows
    }


# ============================================
# Donations
# ============================================

@router.get("/donations")
def donations(
    request: Request
):

    require_section_view(request, "donations")

    columns, rows = get_table_data(
        "donations"
    )

    return {
        "columns": columns,
        "data": rows
    }


# ============================================
# Register Scan (OCR-assisted donation entry)
# ============================================
# Admin uploads a photo of the security-desk
# donation register. Gemini vision extracts
# rows, the admin reviews/corrects them in the
# frontend, then confirmed rows are saved
# through the exact same save + receipt +
# WhatsApp path as an online donation - just
# without a UTR/screenshot, and always as
# "pending" status like the online flow.
# ============================================

REGISTER_SCANS_DIR = "static/register_scans"
os.makedirs(REGISTER_SCANS_DIR, exist_ok=True)


@router.post("/register/scan")
async def admin_scan_register(
    request: Request,
    file: UploadFile = File(...)
):

    require_full_admin(request)

    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(REGISTER_SCANS_DIR, unique_filename)

    contents = await file.read()

    with open(save_path, "wb") as f:
        f.write(contents)

    extracted_rows = extract_register_rows(save_path)

    # Flag rows that fail existing flat-number validation
    # so the admin's eye goes straight to likely OCR errors.
    for row in extracted_rows:

        block = row.get("block")
        flat_number = row.get("flat_number")

        if block and flat_number:
            row["flat_valid"] = validate_flat_number(block, flat_number)
        else:
            row["flat_valid"] = False

    return {
        "extracted_rows": extracted_rows,
        "row_count": len(extracted_rows)
    }


@router.post("/register/confirm")
async def admin_confirm_register_donations(
    request: Request,
    rows: list[dict]
):

    require_full_admin(request)

    results = []

    for row in rows:

        name = (row.get("name") or "").strip()
        block = row.get("block")
        flat_number = (row.get("flat_number") or "").strip()
        amount = row.get("amount")
        mobile = row.get("mobile")
        override_validation = bool(row.get("override_validation"))

        if not name or not amount:

            results.append({
                "row": row,
                "success": False,
                "error": "Missing required field (name or amount)."
            })
            continue

        if not override_validation:

            if not block or not flat_number:

                results.append({
                    "row": row,
                    "success": False,
                    "error": "Missing block or flat number. Check the 'Non-resident / Other' box if this isn't a resident flat."
                })
                continue

            if not validate_flat_number(block, flat_number):

                results.append({
                    "row": row,
                    "success": False,
                    "error": f"Invalid flat number '{flat_number}' for {block} block."
                })
                continue

        try:

            result = donation_service.save_register_donation(
                name=name,
                block=block or "",
                flat_number=flat_number or (row.get("raw_flat_text") or "Other").strip(),
                amount=amount,
                mobile=mobile
            )

            results.append({
                "row": row,
                "success": True,
                "receipt_id": result["receipt_id"],
                "whatsapp_sent": result["whatsapp_sent"]
            })

        except Exception as error:

            results.append({
                "row": row,
                "success": False,
                "error": str(error)
            })

    saved_count = sum(1 for r in results if r["success"])

    log_admin_activity(
        get_current_admin_username(request),
        "register_scan_confirmed",
        f"Saved {saved_count}/{len(rows)} register-scanned donations"
    )

    return {
        "results": results,
        "saved_count": saved_count,
        "total_count": len(rows)
    }


# ============================================
# Cultural Program Sign-up Notebook Scan
# ============================================
# Separate from the donation register scan above - this reads
# the physical sign-up notebook for cultural performances and
# saves entries into the same cultural_registrations table a
# normal app registration uses, so they show up identically in
# this admin panel. track_path is always left empty (None) -
# no performance track was collected on paper, same as a normal
# registration where the track upload is optional. Category is
# not captured on paper, so the admin picks it per row here.
# ============================================

CULTURAL_SIGNUP_SCANS_DIR = "static/register_scans"


@router.post("/cultural-register/scan")
async def admin_scan_cultural_signups(
    request: Request,
    file: UploadFile = File(...)
):

    require_full_admin(request)

    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(CULTURAL_SIGNUP_SCANS_DIR, unique_filename)

    contents = await file.read()

    with open(save_path, "wb") as f:
        f.write(contents)

    extracted_rows = extract_cultural_signup_rows(save_path)

    for row in extracted_rows:

        block = row.get("block")
        flat_number = row.get("flat_number")

        if block and flat_number:
            row["flat_valid"] = validate_flat_number(block, flat_number)
        else:
            row["flat_valid"] = False

    return {
        "extracted_rows": extracted_rows,
        "row_count": len(extracted_rows)
    }


@router.post("/cultural-register/confirm")
async def admin_confirm_cultural_signups(
    request: Request,
    rows: list[dict]
):

    require_full_admin(request)

    results = []

    for row in rows:

        name = (row.get("name") or "").strip()
        mobile = (row.get("mobile") or "").strip() or None
        age = (row.get("age") or "").strip() or None
        block = row.get("block")
        flat_number = (row.get("flat_number") or "").strip()
        categories = (row.get("categories") or "").strip()
        override_validation = bool(row.get("override_validation"))

        if not name:

            results.append({
                "row": row,
                "success": False,
                "error": "Missing name."
            })
            continue

        if not categories:

            results.append({
                "row": row,
                "success": False,
                "error": "Please select at least one category for this entry."
            })
            continue

        if not override_validation:

            if not block or not flat_number:

                results.append({
                    "row": row,
                    "success": False,
                    "error": "Missing block or flat number. Check the 'Non-resident / Other' box if this isn't a resident flat."
                })
                continue

            if not validate_flat_number(block, flat_number):

                results.append({
                    "row": row,
                    "success": False,
                    "error": f"Invalid flat number '{flat_number}' for {block} block."
                })
                continue

        try:

            save_cultural_registration(
                name=name,
                block=block or "",
                flat_number=flat_number or (row.get("raw_flat_text") or "Other").strip(),
                mobile=mobile,
                categories=categories,
                other_details=None,
                track_path=None,
                age=age
            )

            results.append({
                "row": row,
                "success": True
            })

        except Exception as error:

            results.append({
                "row": row,
                "success": False,
                "error": str(error)
            })

    saved_count = sum(1 for r in results if r["success"])

    log_admin_activity(
        get_current_admin_username(request),
        "cultural_signup_scan_confirmed",
        f"Saved {saved_count}/{len(rows)} cultural sign-up entries"
    )

    return {
        "results": results,
        "saved_count": saved_count,
        "total_count": len(rows)
    }


# ============================================
# Annaprasada
# ============================================

@router.get("/annaprasada")
def annaprasada(
    request: Request
):

    require_section_view(request, "annaprasada")

    columns, rows = get_table_data(
        "annaprasada"
    )

    return {
        "columns": columns,
        "data": rows
    }


# ============================================
# Annaprasada Coupon Register Scan
# ============================================
# Same pattern as the donation register scan and cultural
# sign-up scan above: admin uploads a photo of the offline
# coupon-handout register, Gemini extracts rows, the admin
# reviews/corrects them, then confirmed rows are saved through
# the exact same coupon generation + WhatsApp path as an online
# booking (generate_coupon_id, save_annaprasada_booking,
# generate_annaprasada_coupon, send_annaprasada_confirmation) -
# just without a mobile number in most cases, in which case the
# WhatsApp send is silently skipped (same as any booking with no
# reachable number). Every row - online or from this scan - draws
# its serial number from the same single auto-incrementing
# counter, so scanned entries simply continue on from whatever
# the last saved booking's number was; there's no separate
# "offline" numbering.
# ============================================

ANNAPRASADA_SCANS_DIR = "static/register_scans"


@router.post("/annaprasada-register/scan")
async def admin_scan_annaprasada_register(
    request: Request,
    file: UploadFile = File(...)
):

    require_full_admin(request)

    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = os.path.join(ANNAPRASADA_SCANS_DIR, unique_filename)

    contents = await file.read()

    with open(save_path, "wb") as f:
        f.write(contents)

    extracted_rows = extract_annaprasada_rows(save_path)

    for row in extracted_rows:

        block = row.get("block")
        flat_number = row.get("flat_number")

        if block and flat_number:
            row["flat_valid"] = validate_flat_number(block, flat_number)
        else:
            row["flat_valid"] = False

    return {
        "extracted_rows": extracted_rows,
        "row_count": len(extracted_rows)
    }


@router.post("/annaprasada-register/confirm")
async def admin_confirm_annaprasada_register(
    request: Request,
    rows: list[dict]
):

    require_full_admin(request)

    results = []

    for row in rows:

        name = (row.get("name") or "").strip()
        block = row.get("block")
        flat_number = (row.get("flat_number") or "").strip()
        mobile = (row.get("mobile") or "").strip() or None
        override_validation = bool(row.get("override_validation"))

        members_raw = str(row.get("members") or "").strip()

        if not name or not members_raw or not members_raw.isdigit() or int(members_raw) < 1:

            results.append({
                "row": row,
                "success": False,
                "error": "Missing name, or members must be a whole number of 1 or more."
            })
            continue

        members = members_raw

        # Adults/children are rarely on paper - default to
        # "everyone's an adult" (children 0) when not given,
        # same assumption the review table pre-fills so the
        # admin can see and correct it before confirming rather
        # than it being silently guessed here.
        adults_raw = str(row.get("adults") or "").strip()
        children_raw = str(row.get("children") or "").strip()

        if not adults_raw.isdigit() or not children_raw.isdigit() or (int(adults_raw) + int(children_raw)) != int(members):

            adults = members
            children = "0"

        else:

            adults = adults_raw
            children = children_raw

        if not override_validation:

            if not block or not flat_number:

                results.append({
                    "row": row,
                    "success": False,
                    "error": "Missing block or flat number. Check the 'Non-resident / Other' box if this isn't a resident flat."
                })
                continue

            if not validate_flat_number(block, flat_number):

                results.append({
                    "row": row,
                    "success": False,
                    "error": f"Invalid flat number '{flat_number}' for {block} block."
                })
                continue

        try:

            resolved_flat_number = flat_number or (row.get("raw_flat_text") or "Other").strip()

            coupon_id = generate_coupon_id(source="offline")

            serial_number = save_annaprasada_booking(
                coupon_id=coupon_id,
                name=name,
                block=block or "",
                flat_number=resolved_flat_number,
                members=members,
                mobile=mobile,
                adults=adults,
                children=children,
                source="offline"
            )

            verify_url = f"{PUBLIC_BASE_URL}/verify/{coupon_id}"

            coupon_path = generate_annaprasada_coupon(
                coupon_id=coupon_id,
                serial_number=serial_number,
                name=name,
                members=members,
                verify_url=verify_url
            )

            whatsapp_sent = False

            if mobile:

                whatsapp_sent = send_annaprasada_confirmation(
                    name=name,
                    members=members,
                    block=block or "",
                    flat=resolved_flat_number,
                    coupon_id=coupon_id,
                    coupon_image_path=coupon_path,
                    mobile_number=mobile
                )

            results.append({
                "row": row,
                "success": True,
                "coupon_id": coupon_id,
                "serial_number": serial_number,
                "whatsapp_sent": whatsapp_sent
            })

        except Exception as error:

            results.append({
                "row": row,
                "success": False,
                "error": str(error)
            })

    saved_count = sum(1 for r in results if r["success"])

    log_admin_activity(
        get_current_admin_username(request),
        "annaprasada_register_scan_confirmed",
        f"Saved {saved_count}/{len(rows)} register-scanned Annaprasada coupons"
    )

    return {
        "results": results,
        "saved_count": saved_count,
        "total_count": len(rows)
    }


# ============================================
# Export ALL Data
# ============================================

@router.get("/export/all")
def export_all(
    request: Request
):

    require_full_admin(request)

    workbook = create_excel_file()

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=LVS_Festival_Data.xlsx"
        }
    )

# ============================================
# Export Registrations
# ============================================

@router.get("/export/registrations")
def export_registrations(
    request: Request
):

    require_section_view(request, "registrations")

    workbook = create_excel_file(
        only_table="registrations"
    )

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=registrations.xlsx"
        }
    )


# ============================================
# Export Cultural Programs
# ============================================

@router.get("/export/cultural")
def export_cultural(
    request: Request
):

    require_section_view(request, "cultural")

    workbook = create_excel_file(
        only_table="cultural"
    )

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=cultural_programs.xlsx"
        }
    )


# ============================================
# Export Volunteers
# ============================================
# Every per-section export below (registrations, cultural,
# volunteers, donations, annaprasada) uses require_section_view
# rather than require_full_admin: a coordinator login scoped to
# one section (e.g. Cultural, Volunteers) needs to pull their
# own list into Excel for their own reference. Each route still
# only ever returns its own single sheet, and a login scoped to
# a different section is rejected exactly like the matching GET
# view route. Only /export/all (every section combined) stays
# full-admin only.

@router.get("/export/volunteers")
def export_volunteers(
    request: Request
):

    require_section_view(request, "volunteers")

    workbook = create_excel_file(
        only_table="volunteers"
    )

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=volunteers.xlsx"
        }
    )


# ============================================
# Export Donations
# ============================================

@router.get("/export/donations")
def export_donations(
    request: Request
):

    require_section_view(request, "donations")

    workbook = create_excel_file(
        only_table="donations"
    )

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=donations.xlsx"
        }
    )


# ============================================
# Export Annaprasada
# ============================================

@router.get("/export/annaprasada")
def export_annaprasada(
    request: Request
):

    require_section_view(request, "annaprasada")

    workbook = create_excel_file(
        only_table="annaprasada"
    )

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=annaprasada.xlsx"
        }
    )
# ============================================
# View Single Record
# ============================================

@router.get("/record/{table_name}/{record_id}")
def get_single_record(
    table_name: str,
    record_id: int,
    request: Request
):

    require_section_view(request, table_name)


    try:

        record = get_record_by_id(
            table_name,
            record_id
        )


    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


    if record is None:

        raise HTTPException(
            status_code=404,
            detail="Record not found"
        )


    return {
        "table": table_name,
        "record": record
    }

# ============================================
# Update Single Record
# ============================================

@router.put("/record/{table_name}/{record_id}")
async def update_single_record(
    table_name: str,
    record_id: int,
    request: Request
):

    require_full_admin(request)

    try:

        updates = await request.json()

        if not isinstance(updates, dict):

            raise HTTPException(
                status_code=400,
                detail="Invalid update data"
            )


        updated = update_record(
            table_name,
            record_id,
            updates
        )


        if not updated:

            raise HTTPException(
                status_code=404,
                detail="Record not found"
            )

        log_admin_activity(
            get_current_admin_username(request),
            "updated_record",
            f"{table_name} #{record_id}"
        )

        return {
            "success": True,
            "message":
                "Record updated successfully"
        }


    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # ============================================
# Delete Single Record
# ============================================

@router.delete("/record/{table_name}/{record_id}")
def delete_single_record(
    table_name: str,
    record_id: int,
    request: Request
):

    require_full_admin(request)

    try:

        deleted = delete_record(
            table_name,
            record_id
        )

        if not deleted:

            raise HTTPException(
                status_code=404,
                detail="Record not found"
            )

        log_admin_activity(
            get_current_admin_username(request),
            "deleted_record",
            f"{table_name} #{record_id}"
        )

        return {
            "success": True,
            "message":
                "Record deleted successfully"
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============================================
# Activity Log
# ============================================

@router.get("/activity-log")
def activity_log(request: Request):

    require_full_admin(request)

    entries = get_recent_activity_log()

    return {
        "entries": [
            {
                "username": username,
                "action": action,
                "details": details,
                "timestamp": timestamp
            }
            for username, action, details, timestamp in entries
        ]
    }

# ============================================
# Manage Section-Restricted Logins
# (full admin only)
# ============================================

AVAILABLE_SECTIONS = [
    "registrations",
    "cultural",
    "volunteers",
    "donations",
    "annaprasada",
    "announcements",
    "tshirt-orders",
]


class CreateAdminUserRequest(BaseModel):

    name: str
    username: str
    password: str
    section: str = ""   # empty string = full admin


@router.get("/users")
def list_admin_users(request: Request):

    require_full_admin(request)

    rows = get_all_admin_users()

    return {
        "users": [
            {
                "name": name,
                "username": username,
                "section": section,
                "created_at": created_at
            }
            for name, username, section, created_at in rows
        ],
        "available_sections": AVAILABLE_SECTIONS
    }


@router.post("/users")
def create_admin_user(body: CreateAdminUserRequest, request: Request):

    require_full_admin(request)

    name = body.name.strip()
    username = body.username.strip()

    if not name or not username:
        raise HTTPException(
            status_code=400,
            detail="Name and username are required."
        )

    if len(body.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long."
        )

    section = body.section.strip() or None

    if section and section not in AVAILABLE_SECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown section '{section}'."
        )

    if username.lower() == ADMIN_USERNAME.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="That username is reserved for the server's built-in admin account."
        )

    if get_admin_user_by_username(username) is not None:
        raise HTTPException(
            status_code=400,
            detail="That username is already taken."
        )

    add_admin_user(name, username, body.password, section)

    log_admin_activity(
        get_current_admin_username(request),
        "created_admin_user",
        f"{username} (section: {section or 'full admin'})"
    )

    return {"success": True}


@router.delete("/users/{username}")
def remove_admin_user(username: str, request: Request):

    require_full_admin(request)

    if username.strip().lower() == ADMIN_USERNAME.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the server's built-in admin account."
        )

    if username.strip().lower() == get_current_admin_username(request).strip().lower():
        raise HTTPException(
            status_code=400,
            detail="You can't delete the account you're currently logged in as."
        )

    deleted = delete_admin_user(username)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Admin user not found."
        )

    log_admin_activity(
        get_current_admin_username(request),
        "deleted_admin_user",
        username
    )

    return {"success": True}
