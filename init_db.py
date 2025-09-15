from app.database import engine, Base
from app import models

# Create all tables
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
