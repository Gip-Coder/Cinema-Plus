import os
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import models
from backend.auth.security import get_password_hash
from datetime import date

def seed_database():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if we already have movies
        if db.query(models.Movie).first():
            print("Database already seeded!")
            return
            
        print("Seeding Users...")
        admin = models.User(
            username="admin",
            email="admin@cinemaplus.com",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        testuser = models.User(
            username="testuser",
            email="test@user.com",
            hashed_password=get_password_hash("password123"),
            role="customer"
        )
        db.add_all([admin, testuser])
        
        print("Seeding Movies...")
        movies = [
            models.Movie(
                title="Dune: Part Two",
                genre="Sci-Fi",
                language="English",
                format="IMAX 3D",
                release_date=date(2024, 3, 1),
                running_days=45,
                poster_url="https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2JGqqUT1O.jpg",
                description="Paul Atreides unites with Chani and the Fremen while on a warpath of revenge against the conspirators who destroyed his family.",
                duration=166,
                rating=8.8
            ),
            models.Movie(
                title="Oppenheimer",
                genre="Biography",
                language="English",
                format="IMAX 70mm",
                release_date=date(2023, 7, 21),
                running_days=60,
                poster_url="https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
                description="The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
                duration=180,
                rating=8.6
            ),
            models.Movie(
                title="Spider-Man: Across the Spider-Verse",
                genre="Animation",
                language="English",
                format="3D",
                release_date=date(2023, 6, 2),
                running_days=30,
                poster_url="https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg",
                description="Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.",
                duration=140,
                rating=8.7
            )
        ]
        db.add_all(movies)
        
        db.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
