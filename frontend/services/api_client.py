import os
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# Monkey-patch httpx.Response.json to transparently unwrap standard API envelopes
_original_json = httpx.Response.json
def _custom_json(self, *args, **kwargs):
    data = _original_json(self, *args, **kwargs)
    if isinstance(data, dict) and "success" in data and "data" in data and "message" in data:
        return data["data"]
    return data
httpx.Response.json = _custom_json

class APIClient:
    def __init__(self):
        self.token: Optional[str] = None
        self.role: Optional[str] = None
        self.username: Optional[str] = None
        self.client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)

    def set_token(self, token: str):
        self.token = token
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        self.token = None
        self.role = None
        self.username = None
        if "Authorization" in self.client.headers:
            del self.client.headers["Authorization"]
            
    def is_authenticated(self):
        return self.token is not None
        
    def is_admin(self):
        return self.role == "admin"

    # --- Auth ---
    async def login(self, username, password) -> bool:
        response = await self.client.post("/api/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            self.set_token(data["access_token"])
            self.username = username
            # In a real app we might decode the JWT or have a /me endpoint
            # For simplicity, if username is 'admin', we assume role is admin, but best to decode JWT or hit an endpoint.
            # We'll rely on the frontend setting the role manually or decoding JWT.
            from jose import jwt
            try:
                # We don't need the secret key to read the unverified payload
                payload = jwt.get_unverified_claims(data["access_token"])
                self.role = payload.get("role", "customer")
            except Exception as e:
                print(f"Token decode error: {e}")
                self.role = "customer"
            return True
        return False

    async def register(self, username, email, password) -> bool:
        response = await self.client.post("/api/auth/register", json={
            "username": username,
            "email": email,
            "password": password
        })
        return response.status_code == 201

    async def get_me(self) -> Optional[Dict]:
        response = await self.client.get("/api/auth/me")
        if response.status_code == 200:
            return response.json()
        return None

    async def update_profile(self, username: Optional[str] = None, email: Optional[str] = None) -> bool:
        params = {}
        if username: params["username"] = username
        if email: params["email"] = email
        response = await self.client.put("/api/auth/profile", params=params)
        return response.status_code == 200

    async def change_password(self, old_pwd: str, new_pwd: str) -> bool:
        params = {"old_password": old_pwd, "new_password": new_pwd}
        response = await self.client.put("/api/auth/change-password", params=params)
        return response.status_code == 200

    # --- Movies ---
    async def get_movies(self) -> List[Dict]:
        response = await self.client.get("/api/movies/")
        if response.status_code == 200:
            return response.json()
        return []

    async def search_movies(self, q: Optional[str] = None, genre: Optional[str] = None, language: Optional[str] = None) -> List[Dict]:
        params = {}
        if q: params["q"] = q
        if genre: params["genre"] = genre
        if language: params["language"] = language
        
        response = await self.client.get("/api/movies/search", params=params)
        if response.status_code == 200:
            return response.json()
        return []

    async def get_movie(self, movie_id: int) -> Optional[Dict]:
        response = await self.client.get(f"/api/movies/{movie_id}")
        if response.status_code == 200:
            return response.json()
        return None

    # --- Seats & Booking ---
    async def get_booked_seats(self, movie_id: int) -> List[Dict]:
        response = await self.client.get(f"/api/bookings/seats/{movie_id}")
        if response.status_code == 200:
            return response.json()
        return []

    async def book_seats(self, movie_id: int, seats: List[Dict], total_amount: float, show_id: Optional[int] = None) -> Optional[Dict]:
        payload = {
            "movie_id": movie_id,
            "show_id": show_id,
            "total_amount": total_amount,
            "seats": seats
        }
        response = await self.client.post("/api/bookings/book", json=payload)
        if response.status_code == 201:
            return response.json()
        return None
        
    async def get_user_bookings(self) -> List[Dict]:
        response = await self.client.get("/api/bookings/user/bookings")
        if response.status_code == 200:
            return response.json()
        return []

    async def get_seat_price_details(self, show_id: int, category: str) -> Dict:
        response = await self.client.get(f"/api/bookings/price-calculation?show_id={show_id}&category={category}")
        if response.status_code == 200:
            return response.json()
        return {"base_price": 0.0, "applied_rules": [], "final_price": 0.0}
        
    async def download_ticket(self, booking_id: int) -> bytes:
        response = await self.client.get(f"/api/tickets/ticket/{booking_id}/pdf")
        if response.status_code == 200:
            return response.content
        return b""

    # --- Reservations ---
    async def create_reservation(self, show_id: int, seats: List[str]) -> Optional[Dict]:
        payload = {
            "show_id": show_id,
            "seats": seats
        }
        response = await self.client.post("/api/reservations", json=payload)
        if response.status_code == 201:
            return response.json()
        return None

    async def get_reservation(self, group_id: int) -> Optional[Dict]:
        response = await self.client.get(f"/api/reservations/{group_id}")
        if response.status_code == 200:
            return response.json()
        return None

    async def cancel_reservation(self, group_id: int) -> bool:
        response = await self.client.delete(f"/api/reservations/{group_id}")
        return response.status_code == 200

    async def confirm_reservation(self, group_id: int) -> Optional[Dict]:
        response = await self.client.post(f"/api/reservations/{group_id}/confirm")
        if response.status_code in (200, 201):
            return response.json()
        return None

    async def get_show_seat_statuses(self, show_id: int) -> Dict:
        response = await self.client.get(f"/api/shows/{show_id}/seat-status")
        if response.status_code == 200:
            return response.json()
        return {"booked": [], "reserved": []}

    # --- Admin ---
    async def get_admin_stats(self) -> Dict:
        response = await self.client.get("/api/admin/stats")
        if response.status_code == 200:
            return response.json()
        return {}

    async def get_show_stats(self, show_id: int) -> Dict:
        response = await self.client.get(f"/api/admin/shows/{show_id}/stats")
        if response.status_code == 200:
            return response.json()
        return {}
        
    async def create_movie(self, movie_data: Dict) -> bool:
        response = await self.client.post("/api/movies/", json=movie_data)
        return response.status_code == 201
        
    async def delete_movie(self, movie_id: int) -> bool:
        response = await self.client.delete(f"/api/movies/{movie_id}")
        return response.status_code == 204

    async def update_movie(self, movie_id: int, movie_data: Dict) -> bool:
        response = await self.client.put(f"/api/movies/{movie_id}", json=movie_data)
        return response.status_code == 200

    async def get_revenue_chart(self) -> Dict:
        response = await self.client.get("/api/admin/revenue-chart")
        if response.status_code == 200:
            return response.json()
        return {"dates": [], "revenues": []}

    async def get_booking_trends(self) -> Dict:
        response = await self.client.get("/api/admin/booking-trends")
        if response.status_code == 200:
            return response.json()
        return {"dates": [], "counts": []}

    async def get_all_bookings(self) -> List[Dict]:
        response = await self.client.get("/api/admin/bookings")
        if response.status_code == 200:
            return response.json()
        return []

    async def cancel_booking(self, booking_id: int) -> bool:
        response = await self.client.put(f"/api/admin/bookings/{booking_id}/cancel")
        return response.status_code == 200

    async def delete_booking_admin(self, booking_id: int) -> bool:
        response = await self.client.delete(f"/api/admin/bookings/{booking_id}")
        return response.status_code == 200

    async def upload_poster(self, file_content: Optional[bytes] = None, filename: Optional[str] = None, image_url: Optional[str] = None) -> Optional[str]:
        if file_content is not None:
            files = {"file": (filename, file_content, "image/jpeg")}
            response = await self.client.post("/api/movies/upload-poster", files=files)
        elif image_url is not None:
            response = await self.client.post("/api/movies/upload-poster", json={"poster_url": image_url})
        else:
            return None
            
        if response.status_code == 200:
            return response.json().get("poster_url")
        return None

    # --- Schedule ---
    async def create_theatre(self, data: Dict) -> bool:
        response = await self.client.post("/api/admin/theatres", json=data)
        return response.status_code == 200
        
    async def get_theatres(self) -> List[Dict]:
        response = await self.client.get("/api/schedule/theatres")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def create_screen(self, data: Dict) -> bool:
        response = await self.client.post("/api/admin/screens", json=data)
        return response.status_code == 200
        
    async def get_screens(self) -> List[Dict]:
        response = await self.client.get("/api/schedule/screens")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def create_show(self, data: Dict) -> bool:
        response = await self.client.post("/api/schedule/shows", json=data)
        return response.status_code == 200
        
    async def get_shows_by_movie(self, movie_id: int) -> List[Dict]:
        response = await self.client.get(f"/api/schedule/shows/{movie_id}")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def get_show(self, show_id: int) -> Optional[Dict]:
        response = await self.client.get(f"/api/schedule/shows/show/{show_id}")
        if response.status_code == 200:
            return response.json()
        return None
        
    async def get_all_shows(self) -> List[Dict]:
        response = await self.client.get("/api/schedule/shows/all/")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def delete_show(self, show_id: int) -> bool:
        response = await self.client.delete(f"/api/schedule/shows/{show_id}")
        return response.status_code == 200

    # --- Reviews ---
    async def create_review(self, data: Dict) -> bool:
        response = await self.client.post("/api/reviews/", json=data)
        return response.status_code == 201
        
    async def get_movie_reviews(self, movie_id: int) -> List[Dict]:
        response = await self.client.get(f"/api/reviews/movie/{movie_id}")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def get_all_reviews(self) -> List[Dict]:
        response = await self.client.get("/api/reviews/all")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def delete_review(self, review_id: int) -> bool:
        response = await self.client.delete(f"/api/reviews/{review_id}")
        return response.status_code == 200

    # --- Expanded Admin CRUD ---
    async def update_theatre(self, theatre_id: int, data: Dict) -> bool:
        response = await self.client.put(f"/api/admin/theatres/{theatre_id}", json=data)
        return response.status_code == 200
        
    async def delete_theatre(self, theatre_id: int) -> bool:
        response = await self.client.delete(f"/api/admin/theatres/{theatre_id}")
        return response.status_code == 200

    async def update_screen(self, screen_id: int, data: Dict) -> bool:
        response = await self.client.put(f"/api/admin/screens/{screen_id}", json=data)
        return response.status_code == 200

    async def get_pricings(self) -> List[Dict]:
        response = await self.client.get("/api/admin/pricing")
        if response.status_code == 200:
            return response.json()
        return []

    async def update_pricing(self, pricing_id: int, base_price: float, override: bool = False) -> bool:
        headers = {}
        if override:
            headers["X-Admin-Override"] = "true"
        response = await self.client.put(f"/api/admin/pricing/{pricing_id}", json={"base_price": base_price}, headers=headers)
        if response.status_code == 400:
            # Propagate validation failure message to UI
            raise Exception(response.json().get("detail", "Hierarchy pricing validation failed."))
        return response.status_code == 200

    async def create_pricing_rule(self, data: Dict) -> bool:
        response = await self.client.post("/api/admin/pricing/rules", json=data)
        return response.status_code == 200

    async def update_pricing_rule(self, rule_id: int, data: Dict) -> bool:
        response = await self.client.put(f"/api/admin/pricing/rules/{rule_id}", json=data)
        return response.status_code == 200

    async def upload_media_asset(self, file_content: Optional[bytes] = None, filename: Optional[str] = None, asset_type: str = "original", image_url: Optional[str] = None) -> Optional[Dict]:
        if file_content is not None:
            files = {"file": (filename, file_content, "image/jpeg")}
            response = await self.client.post(f"/api/admin/media/upload?asset_type={asset_type}", files=files)
        elif image_url is not None:
            response = await self.client.post(f"/api/admin/media/upload-url", json={"image_url": image_url, "asset_type": asset_type})
        else:
            return None
            
        if response.status_code == 200:
            return response.json()
        return None

    async def delete_media_asset(self, asset_id: int) -> bool:
        response = await self.client.delete(f"/api/admin/media/{asset_id}")
        return response.status_code == 200

    # --- Layouts ---
    async def generate_layout_preview(self, total_seats: int, template: str, custom_cols: Optional[int] = None) -> Optional[Dict]:
        payload = {"total_seats": total_seats, "template": template}
        if custom_cols is not None:
            payload["custom_cols"] = custom_cols
        response = await self.client.post("/api/layouts/generate", json=payload)
        if response.status_code == 200:
            return response.json()
        return None

    async def save_layout(self, screen_id: int, layout_name: str, seats: List[Dict], layout_type: str, rows: int, cols: int) -> Optional[Dict]:
        payload = {
            "screen_id": screen_id,
            "layout_name": layout_name,
            "layout_type": layout_type,
            "seats": seats,
            "rows": rows,
            "cols": cols
        }
        response = await self.client.post("/api/layouts/save", json=payload)
        if response.status_code == 201:
            return response.json()
        return None

    async def get_layout_for_screen(self, screen_id: int) -> Optional[Dict]:
        response = await self.client.get(f"/api/layouts/screen/{screen_id}")
        if response.status_code == 200:
            return response.json()
        return None

    async def get_all_layouts_for_screen(self, screen_id: int) -> List[Dict]:
        response = await self.client.get(f"/api/layouts/screen/{screen_id}/all")
        if response.status_code == 200:
            return response.json()
        return []

    async def get_layout_by_id(self, layout_id: int) -> Optional[Dict]:
        response = await self.client.get(f"/api/layouts/{layout_id}")
        if response.status_code == 200:
            return response.json()
        return None

    async def publish_layout(self, layout_id: int) -> bool:
        response = await self.client.put(f"/api/layouts/{layout_id}/publish")
        return response.status_code == 200

    async def update_layout_seats(self, layout_id: int, seats: List[Dict], rows: int, cols: int) -> Optional[Dict]:
        payload = {
            "seats": seats,
            "rows": rows,
            "cols": cols
        }
        response = await self.client.put(f"/api/layouts/{layout_id}/seats", json=payload)
        if response.status_code == 200:
            return response.json()
        return None

    async def get_layout_stats(self, layout_id: int) -> Dict:
        response = await self.client.get(f"/api/layouts/{layout_id}/stats")
        if response.status_code == 200:
            return response.json()
        return {}

    async def get_layout_templates(self) -> List[Dict]:
        response = await self.client.get("/api/layouts/templates/list")
        if response.status_code == 200:
            return response.json()
        return []

    async def delete_layout(self, layout_id: int) -> bool:
        response = await self.client.delete(f"/api/layouts/{layout_id}")
        return response.status_code == 200

api_client = APIClient()
