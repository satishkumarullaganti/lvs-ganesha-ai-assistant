import os
import secrets
import hmac

from fastapi import (
    APIRouter,
    HTTPException,
    Request
)

from fastapi.responses import (
    StreamingResponse
)

from pydantic import BaseModel

from io import BytesIO

from backend.admin.admin_service import (
    get_dashboard_summary,
    get_table_data,
    create_excel_file
)


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

admin_sessions = set()


# ============================================
# Login Request
# ============================================

class AdminLoginRequest(BaseModel):

    username: str
    password: str


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

    if not ADMIN_PASSWORD:

        raise HTTPException(
            status_code=500,
            detail="Admin password is not configured"
        )

    username_valid = hmac.compare_digest(
        credentials.username,
        ADMIN_USERNAME
    )

    password_valid = hmac.compare_digest(
        credentials.password,
        ADMIN_PASSWORD
    )

    if not username_valid or not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    session_token = secrets.token_urlsafe(
        32
    )

    admin_sessions.add(
        session_token
    )

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

        admin_sessions.discard(
            session_token
        )

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