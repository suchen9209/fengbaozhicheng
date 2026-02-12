"""
Unit tests for database models and operations
"""
import pytest
import tempfile
import os
from datetime import datetime
from app.database import DatabaseManager, AnalysisRecordDB, UserDB


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:///{db_path}"
    manager = DatabaseManager(db_url)
    manager.initialize()
    
    yield manager
    
    # Cleanup
    manager.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestDatabaseManager:
    """Test DatabaseManager"""
    
    def test_initialize_creates_tables(self, temp_db):
        """Test that initialize creates all tables"""
        info = temp_db.get_table_info()
        assert 'analysis_records' in info
        assert 'users' in info
    
    def test_get_session(self, temp_db):
        """Test getting a database session"""
        session = temp_db.get_session()
        assert session is not None
        session.close()
    
    def test_get_session_without_initialize(self):
        """Test getting session without initialization raises error"""
        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.get_session()
    
    def test_table_info(self, temp_db):
        """Test getting table information"""
        info = temp_db.get_table_info()
        
        # Check analysis_records table
        assert 'analysis_records' in info
        columns = info['analysis_records']['columns']
        assert 'id' in columns
        assert 'timestamp' in columns
        assert 'screenshot_path' in columns
        assert 'game_state_json' in columns
        assert 'recommendations_json' in columns
        assert 'user_id' in columns
        assert 'session_id' in columns
        assert 'created_at' in columns


class TestAnalysisRecordDB:
    """Test AnalysisRecordDB model"""
    
    def test_create_record(self, temp_db):
        """Test creating an analysis record"""
        session = temp_db.get_session()
        
        record = AnalysisRecordDB(
            id="test_123",
            timestamp=datetime.utcnow(),
            screenshot_path="uploads/test.png",
            game_state_json='{"species": "人类"}',
            recommendations_json='[]',
            user_id=None,
            session_id="session_456"
        )
        
        session.add(record)
        session.commit()
        
        # Query back
        retrieved = session.query(AnalysisRecordDB).filter_by(id="test_123").first()
        assert retrieved is not None
        assert retrieved.screenshot_path == "uploads/test.png"
        assert retrieved.session_id == "session_456"
        
        session.close()
    
    def test_query_by_session_id(self, temp_db):
        """Test querying records by session_id"""
        session = temp_db.get_session()
        
        # Create multiple records
        for i in range(3):
            record = AnalysisRecordDB(
                id=f"test_{i}",
                timestamp=datetime.utcnow(),
                screenshot_path=f"uploads/test_{i}.png",
                game_state_json='{}',
                recommendations_json='[]',
                session_id="session_123"
            )
            session.add(record)
        
        session.commit()
        
        # Query by session_id
        records = session.query(AnalysisRecordDB).filter_by(session_id="session_123").all()
        assert len(records) == 3
        
        session.close()
    
    def test_query_ordered_by_timestamp(self, temp_db):
        """Test querying records ordered by timestamp"""
        session = temp_db.get_session()
        
        # Create records with different timestamps
        timestamps = [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 2, 10, 0, 0),
            datetime(2024, 1, 3, 10, 0, 0),
        ]
        
        for i, ts in enumerate(timestamps):
            record = AnalysisRecordDB(
                id=f"test_{i}",
                timestamp=ts,
                screenshot_path=f"uploads/test_{i}.png",
                game_state_json='{}',
                recommendations_json='[]',
                session_id="session_123"
            )
            session.add(record)
        
        session.commit()
        
        # Query ordered by timestamp descending
        records = session.query(AnalysisRecordDB).order_by(
            AnalysisRecordDB.timestamp.desc()
        ).all()
        
        assert len(records) == 3
        assert records[0].timestamp == timestamps[2]  # Most recent first
        assert records[2].timestamp == timestamps[0]  # Oldest last
        
        session.close()
    
    def test_delete_record(self, temp_db):
        """Test deleting a record"""
        session = temp_db.get_session()
        
        record = AnalysisRecordDB(
            id="test_delete",
            timestamp=datetime.utcnow(),
            screenshot_path="uploads/test.png",
            game_state_json='{}',
            recommendations_json='[]',
            session_id="session_123"
        )
        
        session.add(record)
        session.commit()
        
        # Delete
        session.delete(record)
        session.commit()
        
        # Verify deleted
        retrieved = session.query(AnalysisRecordDB).filter_by(id="test_delete").first()
        assert retrieved is None
        
        session.close()


class TestUserDB:
    """Test UserDB model"""
    
    def test_create_user(self, temp_db):
        """Test creating a user"""
        session = temp_db.get_session()
        
        user = UserDB(
            id="user_123",
            username="testuser"
        )
        
        session.add(user)
        session.commit()
        
        # Query back
        retrieved = session.query(UserDB).filter_by(id="user_123").first()
        assert retrieved is not None
        assert retrieved.username == "testuser"
        
        session.close()
    
    def test_unique_username(self, temp_db):
        """Test that username must be unique"""
        session = temp_db.get_session()
        
        user1 = UserDB(id="user_1", username="testuser")
        session.add(user1)
        session.commit()
        
        # Try to create another user with same username
        user2 = UserDB(id="user_2", username="testuser")
        session.add(user2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            session.commit()
        
        session.rollback()
        session.close()
