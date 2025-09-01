from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base 
from datetime import datetime
import paho.mqtt.client as mqtt # Import MQTT library
import json # To parse incoming JSON data
import time # For sleep

# --- Database Configuration (Must match Flask's config) ---
DATABASE_URL = "sqlite:///./larvae_monitoring.db" # Relative path assumes it's in the same directory
                                                  # Make sure this path is accessible by this script

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Model for LarvaeData (Replicated from app.py/api.py) ---
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

# Ensure the database table exists
Base.metadata.create_all(bind=engine)
print("Database table 'larvae_data' ensured to exist.")


# --- MQTT Configuration ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "bsf_monitor/larvae_data" # <--- IMPORTANT: This MUST match the topic in your Pi script!

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_message(client, userdata, msg):
    print(f"Received message on topic '{msg.topic}': {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())

        # Validate incoming data (basic check, more robust validation could be added)
        required_keys = ["tray_number", "length", "width", "area", "weight", "count"]
        if not all(key in payload for key in required_keys):
            print("Error: Received payload is missing required keys.")
            return

        # Create a new database session for this message
        db = SessionLocal()
        try:
            new_entry = LarvaeData(
                tray_number=payload["tray_number"],
                length=payload["length"],
                width=payload["width"],
                area=payload["area"],
                weight=payload["weight"],
                count=payload["count"],
                timestamp=datetime.utcnow() # Use current UTC time for consistency
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry) # Refresh to get the generated ID and timestamp
            print(f"Successfully stored data for Tray {new_entry.tray_number}, ID: {new_entry.id}")
        except Exception as e:
            db.rollback() # Rollback the transaction on error
            print(f"Error storing data to database: {e}")
        finally:
            db.close() # Always close the session

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from message: {msg.payload.decode()}")
    except Exception as e:
        print(f"An unexpected error occurred in on_message: {e}")


# --- Main Execution Block ---
if __name__ == "__main__":
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1) # Specify API version
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever() # Blocks and handles reconnections
    except Exception as e:
        print(f"Failed to connect to MQTT broker or loop error: {e}")
    finally:
        print("MQTT subscriber stopped.")