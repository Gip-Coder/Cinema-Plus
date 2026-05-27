import os
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

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

    async def update_profile(self, username: str = None, email: str = None) -> bool:
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

    async def search_movies(self, q: str = None, genre: str = None, language: str = None) -> List[Dict]:
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
        
    async def download_ticket(self, booking_id: int) -> bytes:
        response = await self.client.get(f"/api/tickets/ticket/{booking_id}/pdf")
        if response.status_code == 200:
            return response.content
        return b""

    # --- Admin ---
    async def get_admin_stats(self) -> Dict:
        response = await self.client.get("/api/admin/stats")
        if response.status_code == 200:
            return response.json()
        return {}
        
    async def create_movie(self, movie_data: Dict) -> bool:
        response = await self.client.post("/api/movies/", json=movie_data)
        return response.status_code == 201
        
    async def delete_movie(self, movie_id: int) -> bool:
        response = await self.client.delete(f"/api/movies/{movie_id}")
        return response.status_code == 204

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

    async def upload_poster(self, file_content: bytes, filename: str) -> Optional[str]:
        files = {"file": (filename, file_content, "image/jpeg")}
        response = await self.client.post("/api/movies/upload-poster", files=files)
        if response.status_code == 200:
            return response.json().get("poster_url")
        return None

    # --- Schedule ---
    async def create_theatre(self, data: Dict) -> bool:
        response = await self.client.post("/api/schedule/theatres", json=data)
        return response.status_code == 200
        
    async def get_theatres(self) -> List[Dict]:
        response = await self.client.get("/api/schedule/theatres")
        if response.status_code == 200:
            return response.json()
        return []
        
    async def create_screen(self, theatre_id: int, data: Dict) -> bool:
        response = await self.client.post(f"/api/schedule/screens?theatre_id={theatre_id}", json=data)
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

api_client = APIClient()
