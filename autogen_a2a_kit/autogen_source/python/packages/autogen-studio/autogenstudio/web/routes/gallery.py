# api/routes/gallery.py
from fastapi import APIRouter, Depends, HTTPException

from ...database import DatabaseManager
from ...datamodel import Gallery, Response
from ...gallery.builder import create_default_gallery, create_cohub_gallery
from ..deps import get_db

router = APIRouter()


@router.put("/{gallery_id}")
async def update_gallery_entry(
    gallery_id: int, gallery_data: Gallery, user_id: str, db: DatabaseManager = Depends(get_db)
) -> Response:
    # Check ownership first
    result = db.get(Gallery, filters={"id": gallery_id})
    if not result.status or not result.data:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    if result.data[0].user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this gallery entry")

    # Update if authorized
    gallery_data.id = gallery_id  # Ensure ID matches
    gallery_data.user_id = user_id  # Ensure user_id matches
    return db.upsert(gallery_data)


@router.post("/")
async def create_gallery_entry(gallery_data: Gallery, db: DatabaseManager = Depends(get_db)) -> Response:
    response = db.upsert(gallery_data)
    if not response.status:
        raise HTTPException(status_code=400, detail=response.message)
    return response


def _is_gallery_empty(gallery: Gallery) -> bool:
    """Check if a gallery has empty components (needs to be repopulated)"""
    try:
        config = gallery.config
        if isinstance(config, dict):
            components = config.get("components", {})
        else:
            components = config.components if hasattr(config, "components") else {}

        # Check if all component lists are empty
        if isinstance(components, dict):
            agents = components.get("agents", [])
            models = components.get("models", [])
            tools = components.get("tools", [])
            terminations = components.get("terminations", [])
        else:
            agents = getattr(components, "agents", [])
            models = getattr(components, "models", [])
            tools = getattr(components, "tools", [])
            terminations = getattr(components, "terminations", [])

        return len(agents) == 0 and len(models) == 0 and len(tools) == 0 and len(terminations) == 0
    except Exception:
        return True  # If we can't check, assume it's empty


def _find_gallery_by_id(galleries: list, gallery_id: str) -> tuple:
    """Find a gallery by its config.id and return (gallery, index) or (None, -1)"""
    for i, g in enumerate(galleries):
        try:
            config = g.config
            if isinstance(config, dict):
                gid = config.get("id", "")
            else:
                gid = getattr(config, "id", "")
            if gid == gallery_id:
                return (g, i)
        except Exception:
            continue
    return (None, -1)


@router.get("/")
async def list_gallery_entries(user_id: str, db: DatabaseManager = Depends(get_db)) -> Response:
    try:
        result = db.get(Gallery, filters={"user_id": user_id})
        galleries = result.data if result.data else []

        # Check default gallery
        default_gallery, _ = _find_gallery_by_id(galleries, "gallery_default")
        needs_default_gallery = default_gallery is None or _is_gallery_empty(default_gallery)

        if needs_default_gallery:
            # Delete empty default gallery if exists
            if default_gallery:
                db.delete(Gallery, filters={"id": default_gallery.id})
            # Create default gallery
            gallery_config = create_default_gallery()
            new_default = Gallery(user_id=user_id, config=gallery_config.model_dump())
            db.upsert(new_default)

        # Check AG_COHUB gallery
        cohub_gallery, _ = _find_gallery_by_id(galleries, "gallery_cohub")
        needs_cohub_gallery = cohub_gallery is None or _is_gallery_empty(cohub_gallery)

        if needs_cohub_gallery:
            # Delete empty cohub gallery if exists
            if cohub_gallery:
                db.delete(Gallery, filters={"id": cohub_gallery.id})
            # Create AG_COHUB gallery
            try:
                cohub_config = create_cohub_gallery()
                new_cohub = Gallery(user_id=user_id, config=cohub_config.model_dump())
                db.upsert(new_cohub)
            except Exception as e:
                # Log but don't fail - cohub gallery is optional
                print(f"Warning: Failed to create AG_COHUB gallery: {e}")

        # Re-fetch all galleries
        result = db.get(Gallery, filters={"user_id": user_id})
        return result
    except Exception as e:
        return Response(status=False, data=[], message=f"Error retrieving gallery entries: {str(e)}")


@router.get("/{gallery_id}")
async def get_gallery_entry(gallery_id: int, user_id: str, db: DatabaseManager = Depends(get_db)) -> Response:
    result = db.get(Gallery, filters={"id": gallery_id, "user_id": user_id})
    if not result.status or not result.data:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    return Response(status=result.status, data=result.data[0], message=result.message)


@router.delete("/{gallery_id}")
async def delete_gallery_entry(gallery_id: int, user_id: str, db: DatabaseManager = Depends(get_db)) -> Response:
    # Check ownership first
    result = db.get(Gallery, filters={"id": gallery_id, "user_id": user_id})

    if not result.status or not result.data:
        raise HTTPException(status_code=404, detail="Gallery entry not found")
    response = db.delete(Gallery, filters={"id": gallery_id})
    # Delete if authorized
    return response
