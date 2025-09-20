# database.py - Database Integration for Analysis Results
"""
Bonus Feature: Database integration for storing analysis results and user data
This implements SQLAlchemy models and database operations
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'sqlite:///./financial_analyzer.db'  # Default to SQLite for easy setup
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class AnalysisResult(Base):
    """Model for storing financial analysis results"""
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    query = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    analysis_type = Column(String, default="comprehensive")  # comprehensive, investment, risk
    status = Column(String, default="completed")  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_ip = Column(String, nullable=True)  # For basic user tracking
    job_id = Column(String, nullable=True)  # For queue integration

class UserSession(Base):
    """Model for tracking user sessions and usage"""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, unique=True)
    user_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    analysis_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class SystemMetrics(Base):
    """Model for storing system performance metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, nullable=True)  # JSON string for additional data

# Create all tables
def init_db():
    """Initialize the database with all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database operations
class DatabaseOperations:
    """Class containing database operations for the financial analyzer"""
    
    @staticmethod
    def create_analysis_result(
        db: Session,
        filename: str,
        query: str,
        analysis_result: str,
        original_filename: str = None,
        file_size: int = None,
        analysis_type: str = "comprehensive",
        processing_time: float = None,
        user_ip: str = None,
        job_id: str = None
    ) -> AnalysisResult:
        """Create a new analysis result record"""
        try:
            db_result = AnalysisResult(
                filename=filename,
                original_filename=original_filename or filename,
                file_size=file_size,
                query=query,
                analysis_result=analysis_result,
                analysis_type=analysis_type,
                processing_time=processing_time,
                user_ip=user_ip,
                job_id=job_id
            )
            
            db.add(db_result)
            db.commit()
            db.refresh(db_result)
            
            logger.info(f"Created analysis result with ID: {db_result.id}")
            return db_result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create analysis result: {e}")
            raise
    
    @staticmethod
    def get_analysis_result(db: Session, result_id: str) -> Optional[AnalysisResult]:
        """Get analysis result by ID"""
        try:
            return db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
        except Exception as e:
            logger.error(f"Failed to get analysis result {result_id}: {e}")
            return None
    
    @staticmethod
    def get_analysis_results_by_session(
        db: Session, 
        user_ip: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[AnalysisResult]:
        """Get analysis results for a user session"""
        try:
            query = db.query(AnalysisResult)
            
            if user_ip:
                query = query.filter(AnalysisResult.user_ip == user_ip)
            
            return query.order_by(AnalysisResult.created_at.desc())\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
                       
        except Exception as e:
            logger.error(f"Failed to get analysis results: {e}")
            return []
    
    @staticmethod
    def update_analysis_status(
        db: Session,
        result_id: str,
        status: str,
        error_message: str = None,
        analysis_result: str = None
    ) -> bool:
        """Update analysis result status (useful for queue processing)"""
        try:
            db_result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
            
            if not db_result:
                logger.warning(f"Analysis result {result_id} not found for status update")
                return False
            
            db_result.status = status
            db_result.updated_at = datetime.utcnow()
            
            if error_message:
                db_result.error_message = error_message
            
            if analysis_result:
                db_result.analysis_result = analysis_result
            
            db.commit()
            logger.info(f"Updated analysis result {result_id} status to {status}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update analysis status: {e}")
            return False
    
    @staticmethod
    def create_or_update_session(
        db: Session,
        session_id: str,
        user_ip: str = None,
        user_agent: str = None
    ) -> UserSession:
        """Create or update user session"""
        try:
            session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
            
            if session:
                # Update existing session
                session.last_activity = datetime.utcnow()
                session.analysis_count += 1
            else:
                # Create new session
                session = UserSession(
                    session_id=session_id,
                    user_ip=user_ip,
                    user_agent=user_agent,
                    analysis_count=1
                )
                db.add(session)
            
            db.commit()
            db.refresh(session)
            return session
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create/update session: {e}")
            raise
    
    @staticmethod
    def record_system_metric(
        db: Session,
        metric_name: str,
        metric_value: float,
        metric_unit: str = None,
        metadata: Dict[str, Any] = None
    ) -> SystemMetrics:
        """Record a system performance metric"""
        try:
            metric = SystemMetrics(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            return metric
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record system metric: {e}")
            raise
    
    @staticmethod
    def get_system_metrics(
        db: Session,
        metric_name: str = None,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[SystemMetrics]:
        """Get system metrics"""
        try:
            query = db.query(SystemMetrics)
            
            if metric_name:
                query = query.filter(SystemMetrics.metric_name == metric_name)
            
            # Filter by time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            query = query.filter(SystemMetrics.recorded_at >= cutoff_time)
            
            return query.order_by(SystemMetrics.recorded_at.desc())\
                       .limit(limit)\
                       .all()
                       
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return []
    
    @staticmethod
    def cleanup_old_records(db: Session, days_old: int = 30) -> Dict[str, int]:
        """Clean up old records to manage database size"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Count records to be deleted
            old_analyses = db.query(AnalysisResult)\
                           .filter(AnalysisResult.created_at < cutoff_date)\
                           .count()
            
            old_sessions = db.query(UserSession)\
                          .filter(UserSession.last_activity < cutoff_date)\
                          .count()
            
            old_metrics = db.query(SystemMetrics)\
                         .filter(SystemMetrics.recorded_at < cutoff_date)\
                         .count()
            
            # Delete old records
            db.query(AnalysisResult)\
              .filter(AnalysisResult.created_at < cutoff_date)\
              .delete()
            
            db.query(UserSession)\
              .filter(UserSession.last_activity < cutoff_date)\
              .delete()
            
            db.query(SystemMetrics)\
              .filter(SystemMetrics.recorded_at < cutoff_date)\
              .delete()
            
            db.commit()
            
            cleanup_summary = {
                "analyses_deleted": old_analyses,
                "sessions_deleted": old_sessions,
                "metrics_deleted": old_metrics
            }
            
            logger.info(f"Cleanup completed: {cleanup_summary}")
            return cleanup_summary
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old records: {e}")
            return {"error": str(e)}

# Enhanced main.py endpoints for database integration
"""
Add these endpoints to your main.py for database functionality:

from database import DatabaseOperations, get_db, init_db
from sqlalchemy.orm import Session

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/analysis-history")
async def get_analysis_history(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    user_ip = request.client.host
    results = DatabaseOperations.get_analysis_results_by_session(
        db, user_ip=user_ip, limit=limit, offset=offset
    )
    
    return {
        "results": [
            {
                "id": r.id,
                "filename": r.original_filename,
                "query": r.query,
                "created_at": r.created_at.isoformat(),
                "status": r.status,
                "analysis_type": r.analysis_type
            }
            for r in results
        ],
        "count": len(results)
    }

@app.get("/analysis/{result_id}")
async def get_analysis_by_id(result_id: str, db: Session = Depends(get_db)):
    result = DatabaseOperations.get_analysis_result(db, result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "id": result.id,
        "filename": result.original_filename,
        "query": result.query,
        "analysis": result.analysis_result,
        "created_at": result.created_at.isoformat(),
        "status": result.status,
        "processing_time": result.processing_time
    }

@app.get("/system-stats")
async def get_system_stats(db: Session = Depends(get_db)):
    # Get various system statistics
    total_analyses = db.query(AnalysisResult).count()
    recent_analyses = db.query(AnalysisResult)\
                       .filter(AnalysisResult.created_at >= datetime.utcnow() - timedelta(days=7))\
                       .count()
    
    return {
        "total_analyses": total_analyses,
        "recent_analyses_7days": recent_analyses,
        "database_status": "connected"
    }
"""

if __name__ == "__main__":
    # Initialize database when run directly
    print("Initializing database...")
    init_db()
    
    # Create sample data for testing
    db = SessionLocal()
    try:
        # Test database operations
        db_ops = DatabaseOperations()
        
        # Create a test analysis result
        test_result = db_ops.create_analysis_result(
            db=db,
            filename="test_document.pdf",
            query="Test query",
            analysis_result="Test analysis result",
            analysis_type="test",
            user_ip="127.0.0.1"
        )
        
        print(f"Created test analysis result: {test_result.id}")
        
        # Record a test metric
        test_metric = db_ops.record_system_metric(
            db=db,
            metric_name="test_metric",
            metric_value=100.0,
            metric_unit="count",
            metadata={"test": True}
        )
        
        print(f"Recorded test metric: {test_metric.id}")
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error during database setup: {e}")
    finally:
        db.close()