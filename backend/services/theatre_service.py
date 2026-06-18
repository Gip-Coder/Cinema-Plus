from sqlalchemy.orm import Session
from typing import List, Optional
from backend.repositories.theatre_repository import TheatreRepository
from backend.exceptions.base import NotFoundException, BadRequestException
from backend.models.models import Theatre, Screen, Show, SeatPricing, PricingRule, BookedSeat, Booking, User
from backend.schemas.theatre import TheatreCreate, TheatreUpdate, ScreenCreate, ScreenUpdate, ShowCreate
from backend.schemas.admin import SeatPricingUpdate, PricingRuleCreate, PricingRuleUpdate
from backend.utils.pricing_engine import validate_seat_hierarchy
from backend.utils.cache import cache
from backend.utils.audit_logger import log_action

class TheatreService:
    def __init__(self, db: Session):
        self.theatre_repo = TheatreRepository(db)
        self.db = db

    # --- Theatres ---
    async def get_theatres(self) -> List[Theatre]:
        return self.theatre_repo.get_all_theatres()

    async def create_theatre(self, theatre_data: TheatreCreate, current_user: User, client_ip: str) -> Theatre:
        new_theatre = Theatre(**theatre_data.model_dump())
        theatre = self.theatre_repo.create_theatre(new_theatre)
        
        # Log action
        log_action(
            self.db, current_user.id, "theatre", theatre.id, "create",
            new_value=theatre_data.model_dump(), ip_address=client_ip
        )
        
        # Automatically add default base pricing configurations
        for cat, base_price in [("Normal", 150.0), ("Executive", 220.0), ("Premium", 300.0)]:
            pricing = SeatPricing(
                theatre_id=theatre.id,
                seat_category=cat,
                base_price=base_price
            )
            self.theatre_repo.create_pricing(pricing)
            
        cache.invalidate("movie:*")
        return theatre

    async def update_theatre(self, theatre_id: int, theatre_data: TheatreUpdate, current_user: User, client_ip: str) -> Theatre:
        theatre = self.theatre_repo.get_theatre_by_id(theatre_id)
        if not theatre:
            raise NotFoundException("Theatre not found")
            
        old_val = {c.name: getattr(theatre, c.name) for c in theatre.__table__.columns}
        update_dict = theatre_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(theatre, k, v)
            
        theatre = self.theatre_repo.save(theatre)
        
        log_action(
            self.db, current_user.id, "theatre", theatre_id, "update",
            old_value=old_val, new_value=update_dict, ip_address=client_ip
        )
        cache.invalidate("movie:*")
        return theatre

    async def delete_theatre(self, theatre_id: int, current_user: User, client_ip: str) -> None:
        theatre = self.theatre_repo.get_theatre_by_id(theatre_id)
        if not theatre:
            raise NotFoundException("Theatre not found")
            
        old_val = {c.name: getattr(theatre, c.name) for c in theatre.__table__.columns}
        
        screens = self.theatre_repo.get_screens_by_theatre(theatre_id)
        screen_ids = [s.id for s in screens]
        
        shows = self.theatre_repo.get_all_shows()
        show_ids = [sh.id for sh in shows if sh.screen_id in screen_ids]
        
        if show_ids:
            self.theatre_repo.execute_delete(BookedSeat, BookedSeat.show_id.in_(show_ids))
            self.theatre_repo.execute_delete(Booking, Booking.show_id.in_(show_ids))
            self.theatre_repo.execute_delete(Show, Show.id.in_(show_ids))
            
        self.theatre_repo.delete_pricings_by_theatre(theatre_id)
        self.theatre_repo.delete_rules_by_theatre(theatre_id)
        
        if screen_ids:
            self.theatre_repo.execute_delete(Screen, Screen.id.in_(screen_ids))
            
        self.theatre_repo.delete_theatre(theatre)
        
        log_action(
            self.db, current_user.id, "theatre", theatre_id, "delete",
            old_value=old_val, new_value=None, ip_address=client_ip
        )
        cache.invalidate("movie:*")

    # --- Screens ---
    async def get_screens(self) -> List[Screen]:
        return self.theatre_repo.get_all_screens()

    async def create_screen(self, screen_data: ScreenCreate, current_user: User, client_ip: str) -> Screen:
        new_screen = Screen(**screen_data.model_dump())
        screen = self.theatre_repo.create_screen(new_screen)
        
        log_action(
            self.db, current_user.id, "screen", screen.id, "create",
            new_value=screen_data.model_dump(), ip_address=client_ip
        )
        return screen

    async def update_screen(self, screen_id: int, screen_data: ScreenUpdate, current_user: User, client_ip: str) -> Screen:
        screen = self.theatre_repo.get_screen_by_id(screen_id)
        if not screen:
            raise NotFoundException("Screen not found")
            
        old_val = {c.name: getattr(screen, c.name) for c in screen.__table__.columns}
        update_dict = screen_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(screen, k, v)
            
        screen = self.theatre_repo.save(screen)
        
        log_action(
            self.db, current_user.id, "screen", screen_id, "update",
            old_value=old_val, new_value=update_dict, ip_address=client_ip
        )
        return screen

    # --- Shows ---
    async def create_show(self, show_data: ShowCreate, current_user: User, client_ip: str) -> Show:
        new_show = Show(**show_data.model_dump())
        return self.theatre_repo.create_show(new_show)

    async def get_shows_by_movie(self, movie_id: int) -> List[Show]:
        return self.theatre_repo.get_shows_by_movie(movie_id)

    async def get_all_shows(self) -> List[Show]:
        return self.theatre_repo.get_all_shows()

    async def get_show(self, show_id: int) -> Show:
        show = self.theatre_repo.get_show_by_id(show_id)
        if not show:
            raise NotFoundException("Show not found")
        return show

    async def delete_show(self, show_id: int, current_user: User, client_ip: str) -> None:
        show = self.theatre_repo.get_show_by_id(show_id)
        if not show:
            raise NotFoundException("Show not found")
        self.theatre_repo.delete_show(show)

    # --- Seat Pricing ---
    async def get_pricings(self) -> List[SeatPricing]:
        return self.theatre_repo.get_all_pricings()

    async def update_pricing(self, pricing_id: int, pricing_data: SeatPricingUpdate, current_user: User, admin_override: bool, client_ip: str) -> SeatPricing:
        pricing = self.theatre_repo.get_pricing_by_id(pricing_id)
        if not pricing:
            raise NotFoundException("Pricing configuration not found")
            
        old_val = {"base_price": pricing.base_price}
        
        pricings_query = self.theatre_repo.get_pricings_for_theatre_screen(pricing.theatre_id, pricing.screen_id)
        
        # Simulate update for hierarchy validation
        pricings_sim = []
        for p in pricings_query:
            sim_p = SeatPricing(
                theatre_id=p.theatre_id,
                screen_id=p.screen_id,
                seat_category=p.seat_category,
                base_price=pricing_data.base_price if p.id == pricing_id else p.base_price
            )
            pricings_sim.append(sim_p)
            
        valid, msg = validate_seat_hierarchy(pricings_sim, admin_override=admin_override)
        if not valid:
            raise BadRequestException(msg)
            
        pricing.base_price = pricing_data.base_price
        pricing = self.theatre_repo.save(pricing)
        
        log_action(
            self.db, current_user.id, "pricing", pricing_id, "update",
            old_value=old_val, new_value={"base_price": pricing.base_price}, ip_address=client_ip
        )
        return pricing

    # --- Pricing Rules ---
    async def create_rule(self, rule_data: PricingRuleCreate, current_user: User, client_ip: str) -> PricingRule:
        if rule_data.multiplier <= 0:
            raise BadRequestException("Surge multipliers must be positive numbers greater than 0.")
        if rule_data.valid_from and rule_data.valid_to and rule_data.valid_from > rule_data.valid_to:
            raise BadRequestException("Invalid date ranges. Start date cannot exceed end date.")
            
        new_rule = PricingRule(**rule_data.model_dump())
        rule = self.theatre_repo.create_rule(new_rule)
        
        log_action(
            self.db, current_user.id, "rule", rule.id, "create",
            new_value=rule_data.model_dump(), ip_address=client_ip
        )
        return rule

    async def update_rule(self, rule_id: int, rule_data: PricingRuleUpdate, current_user: User, client_ip: str) -> PricingRule:
        rule = self.theatre_repo.get_rule_by_id(rule_id)
        if not rule:
            raise NotFoundException("Pricing rule not found")
            
        old_val = {c.name: getattr(rule, c.name) for c in rule.__table__.columns if c.name != 'created_at'}
        update_dict = rule_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(rule, k, v)
            
        rule = self.theatre_repo.save(rule)
        
        log_action(
            self.db, current_user.id, "rule", rule_id, "update",
            old_value=old_val, new_value=update_dict, ip_address=client_ip
        )
        return rule
