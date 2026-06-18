from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Any
from backend.models.models import Theatre, Screen, Show, SeatPricing, PricingRule

class TheatreRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Theatres ---
    def get_theatre_by_id(self, theatre_id: int) -> Optional[Theatre]:
        return self.db.query(Theatre).filter(Theatre.id == theatre_id).first()

    def get_all_theatres(self) -> List[Theatre]:
        return self.db.query(Theatre).all()

    def create_theatre(self, theatre: Theatre) -> Theatre:
        self.db.add(theatre)
        self.db.commit()
        self.db.refresh(theatre)
        return theatre

    def delete_theatre(self, theatre: Theatre) -> None:
        self.db.delete(theatre)
        self.db.commit()

    # --- Screens ---
    def get_screen_by_id(self, screen_id: int) -> Optional[Screen]:
        return self.db.query(Screen).filter(Screen.id == screen_id).first()

    def get_screens_by_theatre(self, theatre_id: int) -> List[Screen]:
        return self.db.query(Screen).filter(Screen.theatre_id == theatre_id).all()

    def get_all_screens(self) -> List[Screen]:
        return self.db.query(Screen).all()

    def create_screen(self, screen: Screen) -> Screen:
        self.db.add(screen)
        self.db.commit()
        self.db.refresh(screen)
        return screen

    # --- Shows ---
    def get_show_by_id(self, show_id: int) -> Optional[Show]:
        return self.db.query(Show).options(
            joinedload(Show.movie),
            joinedload(Show.screen)
        ).filter(Show.id == show_id).first()

    def get_shows_by_movie(self, movie_id: int) -> List[Show]:
        return self.db.query(Show).options(
            joinedload(Show.movie),
            joinedload(Show.screen)
        ).filter(Show.movie_id == movie_id).all()

    def get_all_shows(self) -> List[Show]:
        return self.db.query(Show).options(
            joinedload(Show.movie),
            joinedload(Show.screen)
        ).all()

    def create_show(self, show: Show) -> Show:
        self.db.add(show)
        self.db.commit()
        self.db.refresh(show)
        return show

    def delete_show(self, show: Show) -> None:
        self.db.delete(show)
        self.db.commit()

    # --- Seat Pricings ---
    def get_pricing_by_id(self, pricing_id: int) -> Optional[SeatPricing]:
        return self.db.query(SeatPricing).filter(SeatPricing.id == pricing_id).first()

    def get_all_pricings(self) -> List[SeatPricing]:
        return self.db.query(SeatPricing).all()

    def get_pricings_for_theatre_screen(self, theatre_id: int, screen_id: Optional[int]) -> List[SeatPricing]:
        return self.db.query(SeatPricing).filter(
            SeatPricing.theatre_id == theatre_id,
            SeatPricing.screen_id == screen_id
        ).all()

    def create_pricing(self, pricing: SeatPricing) -> SeatPricing:
        self.db.add(pricing)
        self.db.commit()
        self.db.refresh(pricing)
        return pricing

    def delete_pricings_by_theatre(self, theatre_id: int) -> int:
        deleted = self.db.query(SeatPricing).filter(SeatPricing.theatre_id == theatre_id).delete(synchronize_session=False)
        self.db.commit()
        return deleted

    # --- Pricing Rules ---
    def get_rule_by_id(self, rule_id: int) -> Optional[PricingRule]:
        return self.db.query(PricingRule).filter(PricingRule.id == rule_id).first()

    def get_active_rules(self) -> List[PricingRule]:
        return self.db.query(PricingRule).filter(PricingRule.is_active == True).all()

    def create_rule(self, rule: PricingRule) -> PricingRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rules_by_theatre(self, theatre_id: int) -> int:
        deleted = self.db.query(PricingRule).filter(PricingRule.theatre_id == theatre_id).delete(synchronize_session=False)
        self.db.commit()
        return deleted

    # --- Utility ---
    def save(self, obj: Any) -> Any:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def execute_delete(self, model: Any, criteria: Any) -> int:
        deleted = self.db.query(model).filter(criteria).delete(synchronize_session=False)
        self.db.commit()
        return deleted
