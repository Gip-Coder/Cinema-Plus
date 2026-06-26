from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.auth.security import get_current_admin_user
from backend.services.layout_service import LayoutService
from backend.utils.response import standard_response
from backend.schemas.layout import (
    LayoutGenerateRequest, LayoutSaveRequest, LayoutBulkSeatUpdate,
    LayoutValidateRequest, LayoutVersionRequest, LayoutRollbackRequest,
    TheatreLayoutResponse, LayoutPreviewResponse, LayoutStatsResponse,
    LayoutTemplateResponse,
)

router = APIRouter()


def get_layout_service(db: Session = Depends(get_db)) -> LayoutService:
    return LayoutService(db)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# ─── Preview (generate without saving) ──────────────────────────────

@router.post("/preview", response_model=None)
async def preview_layout(
    payload: LayoutGenerateRequest,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Generate a layout preview without persisting to database."""
    preview = await layout_service.generate_preview(
        total_seats=payload.total_seats,
        template=payload.template,
        custom_cols=payload.custom_cols,
    )
    return standard_response(data=preview, message="Layout preview generated")


@router.post("/generate", response_model=None)
async def generate_layout_preview(
    payload: LayoutGenerateRequest,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Alias for /preview — generate a layout preview without persisting."""
    preview = await layout_service.generate_preview(
        total_seats=payload.total_seats,
        template=payload.template,
        custom_cols=payload.custom_cols,
    )
    return standard_response(data=preview, message="Layout preview generated")


# ─── Validate (no persistence) ───────────────────────────────────────

@router.post("/validate", response_model=None)
async def validate_layout_endpoint(
    payload: LayoutValidateRequest,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Validate a layout for duplicates, overlaps, and invalid categories."""
    result = await layout_service.validate_layout_preview(payload.seats)
    message = "Layout is valid" if result["is_valid"] else "Layout validation failed"
    return standard_response(data=result, message=message)


# ─── Save ────────────────────────────────────────────────────────────

@router.post("/save", status_code=status.HTTP_201_CREATED, response_model=None)
async def save_layout(
    request: Request,
    payload: LayoutSaveRequest,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Save a layout as a draft."""
    ip = get_client_ip(request)
    layout = await layout_service.save_layout(payload, current_admin, ip)
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(data=layout_res, message="Layout saved successfully")


# ─── Get published layout for a screen ──────────────────────────────

@router.get("/screen/{screen_id}", response_model=None)
async def get_layout_for_screen(
    screen_id: int,
    layout_service: LayoutService = Depends(get_layout_service),
):
    """Get the published layout for a screen. Returns null data if none published."""
    layout = await layout_service.get_layout_for_screen(screen_id)
    if not layout:
        return standard_response(data=None, message="No published layout for this screen")
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(data=layout_res, message="Layout retrieved successfully")


# ─── Get all layouts for a screen (admin) ────────────────────────────

@router.get("/screen/{screen_id}/all", response_model=None)
async def get_all_layouts_for_screen(
    screen_id: int,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Get all layouts (drafts + published) for a screen."""
    layouts = await layout_service.get_all_layouts_for_screen(screen_id)
    layouts_data = [TheatreLayoutResponse.model_validate(l) for l in layouts]
    return standard_response(data=layouts_data, message="Layouts retrieved successfully")


# ─── Get layout by ID ───────────────────────────────────────────────

@router.get("/{layout_id}", response_model=None)
async def get_layout_by_id(
    layout_id: int,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    layout = await layout_service.get_layout_by_id(layout_id)
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(data=layout_res, message="Layout retrieved successfully")


# ─── Publish ─────────────────────────────────────────────────────────

@router.put("/{layout_id}/publish", response_model=None)
async def publish_layout(
    layout_id: int,
    request: Request,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Publish a draft layout (unpublishes any other for the same screen)."""
    ip = get_client_ip(request)
    layout = await layout_service.publish_layout(layout_id, current_admin, ip)
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(data=layout_res, message="Layout published successfully")


# ─── Version management ──────────────────────────────────────────────

@router.post("/{layout_id}/version", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_layout_version(
    layout_id: int,
    request: Request,
    payload: LayoutVersionRequest = LayoutVersionRequest(),
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Create a new draft version cloned from an existing layout."""
    ip = get_client_ip(request)
    layout = await layout_service.create_new_version(
        layout_id, payload.layout_name, current_admin, ip
    )
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(data=layout_res, message="New layout version created")


@router.post("/screen/{screen_id}/rollback", response_model=None)
async def rollback_layout_version(
    screen_id: int,
    payload: LayoutRollbackRequest,
    request: Request,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Rollback to and publish a previous layout version for a screen."""
    ip = get_client_ip(request)
    layout = await layout_service.rollback_version(
        screen_id, payload.version, current_admin, ip
    )
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(
        data=layout_res,
        message=f"Rolled back to layout version {payload.version}",
    )


# ─── Bulk seat update ────────────────────────────────────────────────

@router.put("/{layout_id}/seats", response_model=None)
async def update_layout_seats(
    layout_id: int,
    payload: LayoutBulkSeatUpdate,
    request: Request,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    """Replace all seats in a layout."""
    ip = get_client_ip(request)
    layout = await layout_service.update_layout_seats(layout_id, payload, current_admin, ip)
    layout_res = TheatreLayoutResponse.model_validate(layout)
    return standard_response(data=layout_res, message="Layout seats updated successfully")


# ─── Stats ───────────────────────────────────────────────────────────

@router.get("/{layout_id}/stats", response_model=None)
async def get_layout_stats(
    layout_id: int,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    stats = await layout_service.get_layout_stats(layout_id)
    return standard_response(data=stats, message="Layout stats retrieved")


# ─── Delete ──────────────────────────────────────────────────────────

@router.delete("/{layout_id}", response_model=None)
async def delete_layout(
    layout_id: int,
    request: Request,
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    ip = get_client_ip(request)
    await layout_service.delete_layout(layout_id, current_admin, ip)
    return standard_response(message="Layout deleted successfully")


# ─── Templates ───────────────────────────────────────────────────────

@router.get("/templates/list", response_model=None)
async def get_templates(
    layout_service: LayoutService = Depends(get_layout_service),
    current_admin=Depends(get_current_admin_user),
):
    templates = await layout_service.get_templates()
    return standard_response(data=templates, message="Templates retrieved")
