from datetime import date, datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.models.models import SeatPricing, PricingRule, Show, Screen
import json

def validate_seat_hierarchy(pricings: List[SeatPricing], admin_override: bool = False) -> Tuple[bool, str]:
    """
    Validates that seat pricing always increases progressively from nearest to farthest:
    Normal <= Executive <= Premium.
    
    If admin_override is True, passes validation but logs warnings.
    """
    normal_price = 0.0
    exec_price = 0.0
    premium_price = 0.0
    
    for p in pricings:
        if p.seat_category == "Normal":
            normal_price = p.base_price
        elif p.seat_category == "Executive":
            exec_price = p.base_price
        elif p.seat_category == "Premium":
            premium_price = p.base_price
            
    # If any pricing category is not set, skip progressive comparison
    if not normal_price or not exec_price or not premium_price:
        return True, "Valid (incomplete pricing setup)"
        
    if normal_price <= exec_price <= premium_price:
        return True, "Valid ascending hierarchy"
        
    if admin_override:
        return True, "Valid via Admin override (ascending hierarchy warning: Normal > Executive or Executive > Premium)"
        
    return False, f"Pricing constraint violation: ascending order must be preserved (Normal ₹{normal_price} <= Executive ₹{exec_price} <= Premium ₹{premium_price})"

def calculate_dynamic_price(
    db: Session,
    show_id: int,
    category: str, # Premium, Executive, Normal
) -> Dict[str, Any]:
    """
    Calculates final dynamic seat price for a show based on active rules:
    1. Base seat-category price
    2. Seat hierarchy validation
    3. Rule checking (surges, weekend, holiday, etc.)
    4. Priority-based stacking multiplier calculations
    5. Final rounded output
    """
    # 1. Fetch Show and Screen details
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        return {"base_price": 0.0, "applied_rules": [], "final_price": 0.0}
        
    # 2. Get base pricing for the theatre and screen
    # Try screen-specific first, fallback to theatre-wide pricing
    pricing = db.query(SeatPricing).filter(
        SeatPricing.theatre_id == show.screen.theatre_id,
        SeatPricing.screen_id == show.screen_id,
        SeatPricing.seat_category == category
    ).first()
    
    if not pricing:
        pricing = db.query(SeatPricing).filter(
            SeatPricing.theatre_id == show.screen.theatre_id,
            SeatPricing.screen_id == None,
            SeatPricing.seat_category == category
        ).first()
        
    if not pricing:
        # Fallback default constants if no configuration exists in DB yet
        default_prices = {"Normal": 150.0, "Executive": 220.0, "Premium": 300.0}
        base_price = default_prices.get(category, 150.0)
    else:
        base_price = pricing.base_price
        
    # 3. Retrieve all applicable pricing rules
    # Check rules matching this theatre, this screen, or global rules (Null values)
    today_date = show.date
    rules = db.query(PricingRule).filter(
        PricingRule.is_active == True,
        (PricingRule.theatre_id == None) | (PricingRule.theatre_id == show.screen.theatre_id),
        (PricingRule.screen_id == None) | (PricingRule.screen_id == show.screen_id)
    ).all()
    
    applied_rules = []
    
    # Filter rules by current date range and type criteria
    applicable_rules = []
    for r in rules:
        # Date validity check
        if r.valid_from and today_date < r.valid_from:
            continue
        if r.valid_to and today_date > r.valid_to:
            continue
            
        # Specific rule type condition checks
        is_matched = False
        if r.rule_type == "weekend":
            # 5 = Saturday, 6 = Sunday
            if today_date.weekday() in (5, 6):
                is_matched = True
        elif r.rule_type == "time_based":
            # Example time-based: check morning/night surges. Hour in show time
            try:
                hour = int(show.start_time.split(':')[0])
                # Late night surge (after 10 PM) or morning discounts
                if hour >= 22 or hour < 12:
                    is_matched = True
            except Exception:
                pass
        else:
            # holiday, event, surge are matched by date validity range
            is_matched = True
            
        if is_matched:
            applicable_rules.append(r)
            
    # 4. Sorting rules by priority descending
    applicable_rules.sort(key=lambda x: x.priority, reverse=True)
    
    final_price = base_price
    
    # 5. Stacking calculation rules
    for r in applicable_rules:
        # If multiplier <= 0, safety override to avoid zero pricing
        mult = max(r.multiplier, 0.01)
        
        # Apply multiplier
        if r.stackable:
            final_price *= mult
            applied_rules.append({"name": r.name, "multiplier": r.multiplier})
        else:
            # If not stackable, only apply if no other rule has stacked, or if it has higher priority
            if len(applied_rules) == 0:
                final_price *= mult
                applied_rules.append({"name": r.name, "multiplier": r.multiplier})
                break # Non-stackable stops further rule processing
                
    # Also include the show's base price multiplier if configured
    if show.price_multiplier != 1.0:
        final_price *= show.price_multiplier
        applied_rules.append({"name": "Show Showtime Multiplier", "multiplier": show.price_multiplier})
        
    return {
        "base_price": round(base_price, 2),
        "applied_rules": applied_rules,
        "final_price": round(final_price, 2)
    }
