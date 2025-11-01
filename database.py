from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, LargeBinary, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os
import json

# Use SQLite by default (no extra dependencies needed)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uploaded_files.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL debugging
)

Base = declarative_base()


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="completed")
    extracted_data = Column(Text, nullable=True)  # Store JSON as text
    file_content = Column(LargeBinary, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        extracted_data_dict = None
        if self.extracted_data:
            try:
                extracted_data_dict = json.loads(self.extracted_data)
            except:
                extracted_data_dict = None
        
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "status": self.status,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "extracted_data": extracted_data_dict,
            "error_message": self.error_message
        }

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

