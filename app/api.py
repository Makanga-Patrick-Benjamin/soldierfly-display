from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- Database Configuration (Must match Flask's config) ---
DATABASE_URL = "sqlite:///./larvae_monitoring.db" # Relative path assumes it's in the same directory

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Model for LarvaeData (Replicated from Flask for FastAPI) ---
class LarvaeData(Base):
    __tablename__ = "larvae_data" # Ensure this matches Flask's model table name

    id = Column(Integer, primary_key=True, index=True)
    tray_number = Column(Integer, nullable=False)
    length = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    area = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    count = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Pydantic Model for incoming data validation ---
class LarvaeDataCreate(BaseModel):
    tray_number: int
    length: float
    width: float
    area: float
    weight: float
    count: int

app = FastAPI()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI Endpoint to receive data ---
@app.post("/api/data/")
async def receive_larvae_data(larvae_data: LarvaeDataCreate):
    db = SessionLocal() # Get a new session for this request
    try:
        new_entry = LarvaeData(
            tray_number=larvae_data.tray_number,
            length=larvae_data.length,
            width=larvae_data.width,
            area=larvae_data.area,
            weight=larvae_data.weight,
            count=larvae_data.count,
            timestamp=datetime.utcnow() # Use UTC for consistency
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry) # Refresh to get the generated ID and timestamp

        return {"status": "success", "message": "Data stored", "data": new_entry.id}
    except Exception as e:
        db.rollback() # Rollback on error
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

# To run this FastAPI app:
# Make sure you are in the directory where api.py is located
# uvicorn api:app --host 0.0.0.0 --port 8001 --reload
# Note: Using a different port (e.g., 8001) from Flask (8000) to avoid conflicts.