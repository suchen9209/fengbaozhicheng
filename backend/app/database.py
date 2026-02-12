"""
Database models and initialization for SQLite
"""
from sqlalchemy import create_engine, Column, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from pathlib import Path

Base = declarative_base()


class AnalysisRecordDB(Base):
    """Analysis record database model"""
    __tablename__ = 'analysis_records'
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    screenshot_path = Column(String, nullable=False)
    game_state_json = Column(Text, nullable=False)
    recommendations_json = Column(Text, nullable=False)
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Create composite indexes
    __table_args__ = (
        Index('idx_timestamp_desc', timestamp.desc()),
        Index('idx_user_session', user_id, session_id),
    )


class UserDB(Base):
    """User database model (optional, for future expansion)"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, database_url: str = "sqlite:///./data/stormgate.db"):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
    
    def initialize(self):
        """
        Initialize database connection and create tables
        
        Creates the database file and all tables if they don't exist
        """
        # Ensure data directory exists
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                Path(db_dir).mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Get a new database session
        
        Returns:
            SQLAlchemy Session object
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
    
    def drop_all_tables(self):
        """Drop all tables (use with caution, mainly for testing)"""
        if self.engine:
            Base.metadata.drop_all(bind=self.engine)
    
    def get_table_info(self) -> dict:
        """Get information about database tables"""
        if not self.engine:
            return {"error": "Database not initialized"}
        
        inspector = self.engine.dialect.get_inspector(self.engine)
        tables = inspector.get_table_names()
        
        info = {}
        for table in tables:
            columns = inspector.get_columns(table)
            indexes = inspector.get_indexes(table)
            info[table] = {
                "columns": [col["name"] for col in columns],
                "indexes": [idx["name"] for idx in indexes]
            }
        
        return info


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Session:
    """
    Dependency function for FastAPI to get database session
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
