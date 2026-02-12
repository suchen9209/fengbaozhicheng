"""
Unit tests for HistoryService
"""
import pytest
from datetime import datetime, timedelta
import uuid

from app.services.history_service import HistoryService
from app.models import AnalysisRecord, GameState, Recommendation, Blueprint
from app.database import DatabaseManager


@pytest.fixture
def temp_db_session():
    """Create a temporary database session for testing"""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:///{db_path}"
    manager = DatabaseManager(db_url)
    manager.initialize()
    
    session = manager.get_session()
    yield session
    
    session.close()
    manager.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_analysis_record():
    """Create a sample analysis record"""
    blueprint = Blueprint(
        name="农场",
        name_en="Farm",
        type="生产建筑",
        dlc="基础版",
        inputs={"木材": 5},
        outputs={"食物": 10},
        values={"food": 4, "fuel": 2, "resolve": 1},
        complexity=2,
        synergy={"species_preferences": ["人类"], "biome_bonuses": {}}
    )
    
    game_state = GameState(
        available_blueprints=["农场", "矿场"],
        resources={"木材": 25, "石料": 15},
        species="人类",
        confidence={"blueprints": 0.85}
    )
    
    recommendation = Recommendation(
        blueprint_name="农场",
        score=78.0,
        rank=1,
        reasoning="测试推荐理由",
        details=blueprint
    )
    
    return AnalysisRecord(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        screenshot_path="uploads/test.png",
        game_state=game_state,
        recommendations=[recommendation],
        user_id=None,
        session_id="test_session"
    )


class TestHistoryService:
    """Test HistoryService"""
    
    def test_save_record(self, temp_db_session, sample_analysis_record):
        """Test saving an analysis record"""
        service = HistoryService(temp_db_session)
        
        record_id = service.save_record(sample_analysis_record)
        assert record_id == sample_analysis_record.id
        
        # Verify saved
        retrieved = service.get_record_by_id(record_id)
        assert retrieved is not None
        assert retrieved.id == sample_analysis_record.id
        assert retrieved.session_id == "test_session"
    
    def test_get_records_empty(self, temp_db_session):
        """Test getting records from empty database"""
        service = HistoryService(temp_db_session)
        records = service.get_records()
        assert len(records) == 0
    
    def test_get_records_with_pagination(self, temp_db_session, sample_analysis_record):
        """Test getting records with pagination"""
        service = HistoryService(temp_db_session)
        
        # Create multiple records
        for i in range(5):
            record = AnalysisRecord(
                id=f"test_{i}",
                timestamp=datetime.utcnow(),
                screenshot_path=f"uploads/test_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="test_session"
            )
            service.save_record(record)
        
        # Get first 3 records
        records = service.get_records(limit=3, offset=0)
        assert len(records) == 3
        
        # Get next 2 records
        records = service.get_records(limit=3, offset=3)
        assert len(records) == 2
    
    def test_get_records_by_session_id(self, temp_db_session, sample_analysis_record):
        """Test filtering records by session_id"""
        service = HistoryService(temp_db_session)
        
        # Create records with different session IDs
        for i in range(3):
            record = AnalysisRecord(
                id=f"session1_{i}",
                timestamp=datetime.utcnow(),
                screenshot_path=f"uploads/test_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="session_1"
            )
            service.save_record(record)
        
        for i in range(2):
            record = AnalysisRecord(
                id=f"session2_{i}",
                timestamp=datetime.utcnow(),
                screenshot_path=f"uploads/test_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="session_2"
            )
            service.save_record(record)
        
        # Get records for session_1
        records = service.get_records(session_id="session_1")
        assert len(records) == 3
        
        # Get records for session_2
        records = service.get_records(session_id="session_2")
        assert len(records) == 2
    
    def test_get_records_ordered_by_timestamp(self, temp_db_session, sample_analysis_record):
        """Test that records are ordered by timestamp descending"""
        service = HistoryService(temp_db_session)
        
        timestamps = [
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 2, 10, 0, 0),
            datetime(2024, 1, 3, 10, 0, 0),
        ]
        
        # Create records with specific timestamps
        for i, ts in enumerate(timestamps):
            record = AnalysisRecord(
                id=f"test_{i}",
                timestamp=ts,
                screenshot_path=f"uploads/test_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="test_session"
            )
            service.save_record(record)
        
        # Get records
        records = service.get_records()
        
        # Verify order (most recent first)
        assert len(records) == 3
        assert records[0].timestamp == timestamps[2]
        assert records[1].timestamp == timestamps[1]
        assert records[2].timestamp == timestamps[0]
    
    def test_get_record_by_id_not_found(self, temp_db_session):
        """Test getting non-existent record"""
        service = HistoryService(temp_db_session)
        record = service.get_record_by_id("nonexistent")
        assert record is None
    
    def test_delete_record(self, temp_db_session, sample_analysis_record):
        """Test deleting a record"""
        service = HistoryService(temp_db_session)
        
        # Save record
        record_id = service.save_record(sample_analysis_record)
        
        # Verify exists
        assert service.get_record_by_id(record_id) is not None
        
        # Delete
        result = service.delete_record(record_id)
        assert result is True
        
        # Verify deleted
        assert service.get_record_by_id(record_id) is None
    
    def test_delete_record_not_found(self, temp_db_session):
        """Test deleting non-existent record"""
        service = HistoryService(temp_db_session)
        result = service.delete_record("nonexistent")
        assert result is False
    
    def test_cleanup_old_records(self, temp_db_session, sample_analysis_record):
        """Test cleaning up old records"""
        service = HistoryService(temp_db_session)
        
        # Create old records (35 days ago)
        old_timestamp = datetime.utcnow() - timedelta(days=35)
        for i in range(3):
            record = AnalysisRecord(
                id=f"old_{i}",
                timestamp=old_timestamp,
                screenshot_path=f"uploads/old_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="test_session"
            )
            service.save_record(record)
        
        # Create recent records (5 days ago)
        recent_timestamp = datetime.utcnow() - timedelta(days=5)
        for i in range(2):
            record = AnalysisRecord(
                id=f"recent_{i}",
                timestamp=recent_timestamp,
                screenshot_path=f"uploads/recent_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="test_session"
            )
            service.save_record(record)
        
        # Cleanup records older than 30 days
        deleted_count = service.cleanup_old_records(days=30)
        assert deleted_count == 3
        
        # Verify only recent records remain
        remaining = service.get_records()
        assert len(remaining) == 2
    
    def test_get_total_count(self, temp_db_session, sample_analysis_record):
        """Test getting total count of records"""
        service = HistoryService(temp_db_session)
        
        # Create records
        for i in range(5):
            record = AnalysisRecord(
                id=f"test_{i}",
                timestamp=datetime.utcnow(),
                screenshot_path=f"uploads/test_{i}.png",
                game_state=sample_analysis_record.game_state,
                recommendations=sample_analysis_record.recommendations,
                session_id="test_session"
            )
            service.save_record(record)
        
        # Get total count
        count = service.get_total_count()
        assert count == 5
        
        # Get count for specific session
        count = service.get_total_count(session_id="test_session")
        assert count == 5
        
        count = service.get_total_count(session_id="nonexistent")
        assert count == 0
