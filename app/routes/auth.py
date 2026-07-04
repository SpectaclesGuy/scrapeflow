from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.user_schema import LoginRequest, SignupRequest
from app.services.auth_service import (
    authenticate_user,
    clear_user_session,
    get_or_create_google_user,
    require_session_user,
    set_user_session,
    signup_user,
)
from app.utils.response import success_response

router = APIRouter(prefix='/auth', tags=['auth'])
settings = get_settings()


def _get_google_client():
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Google authentication is not configured',
        )
    try:
        from authlib.integrations.starlette_client import OAuth
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Authlib is not installed',
        ) from exc
    oauth = OAuth()
    oauth.register(
        'google',
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid profile email'},
    )
    return oauth.create_client('google')


@router.post('/signup')
def signup(payload: SignupRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    user = signup_user(db, payload)
    session_user = set_user_session(request, user)
    return success_response('Account created successfully', session_user)


@router.post('/login')
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    user = authenticate_user(db, payload)
    session_user = set_user_session(request, user)
    return success_response('Logged in successfully', session_user)


@router.post('/logout')
def logout(request: Request) -> dict:
    clear_user_session(request)
    return success_response('Logged out successfully', {'ok': True})


@router.get('/me')
def me(request: Request) -> dict:
    user = require_session_user(request)
    return success_response('Session fetched successfully', user)


@router.get('/google/login')
async def google_login(request: Request):
    google = _get_google_client()
    redirect_uri = request.url_for('google_callback')
    return await google.authorize_redirect(request, str(redirect_uri))


@router.get('/google/callback', name='google_callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    google = _get_google_client()
    token = await google.authorize_access_token(request)
    userinfo = token.get('userinfo')
    if not userinfo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Google user info missing')
    email = userinfo.get('email')
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Google account email missing')
    name = userinfo.get('name') or email.split('@')[0]
    user = get_or_create_google_user(db, email=email, name=name)
    session_user = set_user_session(request, user)
    session_json = json.dumps(session_user)
    html = f"""<!DOCTYPE html>
<html lang='en'>
  <body>
    <script>
      localStorage.setItem('scrapeflow:session', {session_json!r});
      window.location.replace('/chat');
    </script>
  </body>
</html>"""
    return HTMLResponse(html)
