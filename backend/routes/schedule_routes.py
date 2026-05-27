from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.models import Theatre, Screen, Show
from backend.schemas.schemas import TheatreBase, TheatreResponse, ScreenBase, ScreenResponse, ShowCreate, ShowResponse
from backend.auth.security import get_current_admin_user

router = APIRouter()

# --- Theatres ---
@router.post("/theatres", response_model=TheatreResponse)
async def create_theatre(theatre: TheatreBase, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_theatre = Theatre(**theatre.model_dump())
    db.add(db_theatre)
    db.commit()
    db.refresh(db_theatre)
    return db_theatre

@router.get("/theatres", response_model=List[TheatreResponse])
async def get_theatres(db: Session = Depends(get_db)):
    return db.query(Theatre).all()

# --- Screens ---
@router.post("/screens", response_model=ScreenResponse)
async def create_screen(screen: ScreenBase, theatre_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_screen = Screen(**screen.model_dump(), theatre_id=theatre_id)
    db.add(db_screen)
    db.commit()
    db.refresh(db_screen)
    return db_screen

@router.get("/screens", response_model=List[ScreenResponse])
async def get_screens(db: Session = Depends(get_db)):
    return db.query(Screen).all()

# --- Shows ---
@router.post("/shows", response_model=ShowResponse)
async def create_show(show: ShowCreate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_show = Show(**show.model_dump())
    db.add(db_show)
    db.commit()
    db.refresh(db_show)
    return db_show

@router.get("/shows/{movie_id}", response_model=List[ShowResponse])
async def get_shows_by_movie(movie_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return db.query(Show).options(
        joinedload(Show.movie),
        joinedload(Show.screen)
    ).filter(Show.movie_id == movie_id).all()

@router.get("/shows/all/", response_model=List[ShowResponse])
async def get_all_shows(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return db.query(Show).options(
        joinedload(Show.movie),
        joinedload(Show.screen)
    ).all()

@router.get("/shows/show/{show_id}", response_model=ShowResponse)
async def get_show(show_id: int, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    show = db.query(Show).options(
        joinedload(Show.movie),
        joinedload(Show.screen)
    ).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show

@router.delete("/shows/{show_id}")
async def delete_show(show_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_show = db.query(Show).filter(Show.id == show_id).first()
    if not db_show:
        raise HTTPException(status_code=404, detail="Show not found")
    db.delete(db_show)
    db.commit()
    return {"message": "Deleted"}
