"""
Database models and connection for storing financial analysis results
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# Create SQLite database
DATABASE_URL = "sqlite:///./financial_analysis.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    verification_result = Column(Text, nullable=True)
    financial_analysis = Column(Text, nullable=True)
    investment_analysis = Column(Text, nullable=True)
    risk_assessment = Column(Text, nullable=True)
    full_result = Column(Text, nullable=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Integer, nullable=True)  # seconds

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
    print(" Database initialized")

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Save analysis to database
def save_analysis(filename: str, query: str, result: str, processing_time: int = None):
    """Save analysis result to database"""
    db = SessionLocal()
    try:
        analysis = AnalysisResult(
            filename=filename,
            query=query,
            full_result=str(result),
            processing_time=processing_time
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        print(f" Analysis saved to database with ID: {analysis.id}")
        return analysis.id
    except Exception as e:
        print(f"Error saving to database: {e}")
        db.rollback()
        return None
    finally:
        db.close()

# Get all analyses
def get_all_analyses(limit: int = 50):
    """Get all analysis results"""
    db = SessionLocal()
    try:
        return db.query(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(limit).all()
    finally:
        db.close()

# Get analysis by ID
def get_analysis_by_id(analysis_id: str):
    """Get specific analysis by ID"""
    db = SessionLocal()
    try:
        return db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()