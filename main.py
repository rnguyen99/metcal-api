"""FastAPI application entry point."""
from __future__ import annotations

import time
from typing import Any, List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from auth import authenticate_user, create_access_token, get_current_user
from config import get_settings
from database import (
    create_asset,
    fetch_all_assets,
    fetch_asset_by_id,
    get_db,
    update_asset,
)
from logger import configure_logging, get_logger
from models import (
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    ErrorResponse,
    TokenRequest,
    TokenResponse,
)

configure_logging()
LOGGER = get_logger("api")
SETTINGS = get_settings()

app = FastAPI(title="Asset API", version="1.0.0")
allow_all_origins = "*" in SETTINGS.cors_allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else SETTINGS.cors_allow_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response_status = 500
    try:
        response = await call_next(request)
        response_status = response.status_code
        return response
    finally:
        process_time = (time.perf_counter() - start_time) * 1000
        user = getattr(request.state, "user", {})
        LOGGER.info(
            "%s %s completed in %.2fms status=%s user=%s",
            request.method,
            request.url.path,
            process_time,
            response_status,
            user.get("username"),
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    LOGGER.warning("Validation error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid request"})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    LOGGER.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})


@app.post("/api/token", response_model=TokenResponse, responses={401: {"model": ErrorResponse}})
async def login_for_access_token(payload: TokenRequest, db_conn=Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db_conn, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(user_id=user["id"], username=user["username"])
    return TokenResponse(access_token=access_token)


@app.get(
    "/api/assets",
    response_model=List[AssetResponse],
    responses={401: {"model": ErrorResponse}},
)
async def list_assets(current_user: dict = Depends(get_current_user), db_conn=Depends(get_db)) -> List[AssetResponse]:
    assets = [AssetResponse(id=row["id"], name=row["name"]) for row in fetch_all_assets(db_conn)]
    return assets


@app.get(
    "/api/asset/{asset_id}",
    response_model=AssetResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_asset(asset_id: int, current_user: dict = Depends(get_current_user), db_conn=Depends(get_db)) -> AssetResponse:
    row = fetch_asset_by_id(db_conn, asset_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetResponse(id=row["id"], name=row["name"])


@app.post(
    "/api/asset",
    status_code=status.HTTP_201_CREATED,
    response_model=AssetResponse,
    responses={401: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def create_asset_endpoint(
    payload: AssetCreate,
    current_user: dict = Depends(get_current_user),
    db_conn=Depends(get_db),
) -> AssetResponse:
    new_id = create_asset(db_conn, payload.name)
    return AssetResponse(id=new_id, name=payload.name)


@app.put(
    "/api/asset/{asset_id}",
    response_model=AssetResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def update_asset_endpoint(
    asset_id: int,
    payload: AssetUpdate,
    current_user: dict = Depends(get_current_user),
    db_conn=Depends(get_db),
) -> AssetResponse:
    updated = update_asset(db_conn, asset_id, payload.name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetResponse(id=asset_id, name=payload.name)
