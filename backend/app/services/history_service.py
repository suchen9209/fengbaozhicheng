"""
History service for managing analysis records
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import datetime, timedelta
import json
import uuid

from app.database import AnalysisRecordDB
from app.models import AnalysisRecord, GameState, Recommendation


class HistoryService:
    """Service for managing analysis history records"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def save_record(self, record: AnalysisRecord) -> str:
        """
        Save an analysis record to the database
        
        Args:
            record: AnalysisRecord object to save
        
        Returns:
            Record ID
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Convert GameState and Recommendations to JSON
            game_state_json = json.dumps({
                "available_blueprints": record.game_state.available_blueprints,
                "resources": record.game_state.resources,
                "species": record.game_state.species,
                "confidence": record.game_state.confidence
            }, ensure_ascii=False)
            
            recommendations_json = json.dumps([
                {
                    "blueprint_name": rec.blueprint_name,
                    "score": rec.score,
                    "rank": rec.rank,
                    "reasoning": rec.reasoning,
                    "details": {
                        "name": rec.details.name,
                        "name_en": rec.details.name_en,
                        "type": rec.details.type,
                        "dlc": rec.details.dlc,
                        "inputs": rec.details.inputs,
                        "outputs": rec.details.outputs,
                        "values": rec.details.values,
                        "complexity": rec.details.complexity,
                        "synergy": rec.details.synergy,
                        "description": rec.details.description
                    }
                }
                for rec in record.recommendations
            ], ensure_ascii=False)
            
            # Create database record
            db_record = AnalysisRecordDB(
                id=record.id,
                timestamp=record.timestamp,
                screenshot_path=record.screenshot_path,
                game_state_json=game_state_json,
                recommendations_json=recommendations_json,
                user_id=record.user_id,
                session_id=record.session_id
            )
            
            self.db.add(db_record)
            self.db.commit()
            self.db.refresh(db_record)
            
            return db_record.id
        
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_records(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[AnalysisRecord]:
        """
        Get analysis records with filtering and pagination
        
        Args:
            user_id: Filter by user ID (optional)
            session_id: Filter by session ID (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip
        
        Returns:
            List of AnalysisRecord objects, ordered by timestamp descending
        """
        query = self.db.query(AnalysisRecordDB)
        
        # Apply filters
        if user_id is not None:
            query = query.filter(AnalysisRecordDB.user_id == user_id)
        if session_id is not None:
            query = query.filter(AnalysisRecordDB.session_id == session_id)
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(AnalysisRecordDB.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        db_records = query.all()
        
        # Convert to AnalysisRecord objects
        records = []
        for db_record in db_records:
            try:
                record = self._db_record_to_analysis_record(db_record)
                records.append(record)
            except (json.JSONDecodeError, KeyError) as e:
                # Log error but continue with other records
                print(f"Warning: Failed to parse record {db_record.id}: {e}")
                continue
        
        return records
    
    def get_record_by_id(self, record_id: str) -> Optional[AnalysisRecord]:
        """
        Get a single analysis record by ID
        
        Args:
            record_id: Record ID
        
        Returns:
            AnalysisRecord object or None if not found
        """
        db_record = self.db.query(AnalysisRecordDB).filter_by(id=record_id).first()
        
        if db_record is None:
            return None
        
        try:
            return self._db_record_to_analysis_record(db_record)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse record {record_id}: {e}")
            return None
    
    def delete_record(self, record_id: str) -> bool:
        """
        Delete an analysis record
        
        Args:
            record_id: Record ID to delete
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db_record = self.db.query(AnalysisRecordDB).filter_by(id=record_id).first()
            
            if db_record is None:
                return False
            
            self.db.delete(db_record)
            self.db.commit()
            return True
        
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def cleanup_old_records(self, days: int = 30) -> int:
        """
        Delete records older than specified days
        
        Args:
            days: Number of days to keep (default: 30)
        
        Returns:
            Number of records deleted
        
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query old records
            old_records = self.db.query(AnalysisRecordDB).filter(
                AnalysisRecordDB.timestamp < cutoff_date
            ).all()
            
            count = len(old_records)
            
            # Delete old records
            for record in old_records:
                self.db.delete(record)
            
            self.db.commit()
            return count
        
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_total_count(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Get total count of records matching filters
        
        Args:
            user_id: Filter by user ID (optional)
            session_id: Filter by session ID (optional)
        
        Returns:
            Total count of matching records
        """
        query = self.db.query(AnalysisRecordDB)
        
        if user_id is not None:
            query = query.filter(AnalysisRecordDB.user_id == user_id)
        if session_id is not None:
            query = query.filter(AnalysisRecordDB.session_id == session_id)
        
        return query.count()
    
    def _db_record_to_analysis_record(self, db_record: AnalysisRecordDB) -> AnalysisRecord:
        """
        Convert database record to AnalysisRecord object
        
        Args:
            db_record: Database record
        
        Returns:
            AnalysisRecord object
        
        Raises:
            json.JSONDecodeError: If JSON parsing fails
            KeyError: If required field is missing
        """
        # Parse game state
        game_state_data = json.loads(db_record.game_state_json)
        game_state = GameState(
            available_blueprints=game_state_data["available_blueprints"],
            resources=game_state_data["resources"],
            species=game_state_data["species"],
            confidence=game_state_data.get("confidence", {})
        )
        
        # Parse recommendations
        recommendations_data = json.loads(db_record.recommendations_json)
        recommendations = []
        
        for rec_data in recommendations_data:
            from app.models import Blueprint
            
            details_data = rec_data["details"]
            details = Blueprint(
                name=details_data["name"],
                name_en=details_data["name_en"],
                type=details_data["type"],
                dlc=details_data["dlc"],
                inputs=details_data["inputs"],
                outputs=details_data["outputs"],
                values=details_data["values"],
                complexity=details_data["complexity"],
                synergy=details_data["synergy"],
                description=details_data.get("description", "")
            )
            
            recommendation = Recommendation(
                blueprint_name=rec_data["blueprint_name"],
                score=rec_data["score"],
                rank=rec_data["rank"],
                reasoning=rec_data["reasoning"],
                details=details
            )
            recommendations.append(recommendation)
        
        # Create AnalysisRecord
        return AnalysisRecord(
            id=db_record.id,
            timestamp=db_record.timestamp,
            screenshot_path=db_record.screenshot_path,
            game_state=game_state,
            recommendations=recommendations,
            user_id=db_record.user_id,
            session_id=db_record.session_id
        )
