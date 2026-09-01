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
    change_admin_password
)

from backend.register_ocr_service import extract_register_rows
from backend.validators import validate_flat_number
from backend.donation_service import donation_service

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
# Get Current Admin Username
# ============================================

def get_current_admin_username(request: Request):

    session_token = request.cookies.get("admin_session")

    return admin_sessions.get(session_token, "unknown")


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

    else:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    session_token = secrets.token_urlsafe(
        32
    )

    admin_sessions[session_token] = logged_in_username

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
        "authenticated": authenticated
    }


# ============================================
# Dashboard Summary
# ============================================

@router.get("/dashboard")
def dashboard(
    request: Request
):

    require_admin(request)

    return get_dashboard_summary()


# ============================================
# Registrations
# ============================================

@router.get("/registrations")
def registrations(
    request: Request
):

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

    results = []

    for row in rows:

        name = (row.get("name") or "").strip()
        block = row.get("block")
        flat_number = (row.get("flat_number") or "").strip()
        amount = row.get("amount")
        mobile = row.get("mobile")

        if not name or not block or not flat_number or not amount:

            results.append({
                "row": row,
                "success": False,
                "error": "Missing required field (name, block, flat_number, or amount)."
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
                block=block,
                flat_number=flat_number,
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
# Annaprasada
# ============================================

@router.get("/annaprasada")
def annaprasada(
    request: Request
):

    require_admin(request)

    columns, rows = get_table_data(
        "annaprasada"
    )

    return {
        "columns": columns,
        "data": rows
    }


# ============================================
# Export ALL Data
# ============================================

@router.get("/export/all")
def export_all(
    request: Request
):

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

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

@router.get("/export/volunteers")
def export_volunteers(
    request: Request
):

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)


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

    require_admin(request)

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

    require_admin(request)

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

    require_admin(request)

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