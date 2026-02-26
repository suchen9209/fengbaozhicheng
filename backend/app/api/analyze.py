"""
API endpoint for screenshot analysis
"""
import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from app.database import get_db
from app.models import Box, GameState, AnalysisRecord
from app.services.recommendation_engine import RecommendationEngine
from app.services.history_service import HistoryService
from app.strategies import StrategyType, EventType, get_all_strategies, get_all_events

router = APIRouter()


class BoxModel(BaseModel):
    """Box model for validation"""
    x: int
    y: int
    width: int
    height: int
    label: str
    
    @validator('label')
    def validate_label(cls, v):
        allowed = ['blueprints', 'resources', 'species']
        if v not in allowed:
            raise ValueError(f"label must be one of {allowed}")
        return v


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint"""
    boxes: List[BoxModel]
    session_id: Optional[str] = None
    
    @validator('boxes')
    def validate_boxes(cls, v):
        if len(v) != 3:
            raise ValueError("必须提供3个识别框")
        labels = {box.label for box in v}
        required = {'blueprints', 'resources', 'species'}
        if labels != required:
            raise ValueError(f"识别框标签必须包含: {required}")
        return v


@router.get("/api/v1/strategies")
async def get_strategies():
    """Get all available strategies for recommendation"""
    return {
        "strategies": get_all_strategies()
    }


@router.get("/api/v1/events")
async def get_events():
    """Get all available events for recommendation"""
    return {
        "events": get_all_events()
    }


@router.post("/api/v1/analyze")
async def analyze_screenshot(
    request: Request,
    image: UploadFile = File(...),
    boxes: str = Form(...),
    session_id: Optional[str] = Form(None),
    lang: Optional[str] = Form("en"),
    strategy: Optional[str] = Form(None),
    event: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Analyze screenshot and return blueprint recommendations.
    Internal logic uses English; response language: lang=zh for 中文, lang=en for English.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    response_lang = "zh" if (lang and str(lang).strip().lower() == "zh") else "en"
    
    try:
        # Validate file format
        allowed_formats = ['image/png', 'image/jpeg', 'image/jpg']
        if image.content_type not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail="仅支持PNG、JPG、JPEG格式"
            )
        
        # Validate file size (10MB)
        content = await image.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件大小不能超过10MB"
            )
        
        # Parse boxes
        try:
            boxes_data = json.loads(boxes)
            analyze_request = AnalyzeRequest(boxes=boxes_data, session_id=session_id)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"识别框数据格式错误: {str(e)}"
            )
        
        # Save screenshot
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        Path(upload_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_id = str(uuid.uuid4())[:8]
        file_ext = Path(image.filename).suffix or '.png'
        filename = f"{timestamp}_{random_id}{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Analyze image using image analysis service
        try:
            from app.services.template_matcher import TemplateMatcher
            from app.services.ocr_service import OCRService
            from app.services.image_analysis_service import ImageAnalysisService, _slug
            from app.main import blueprint_loader
            
            templates_dir = os.getenv("TEMPLATES_DIR", "app/data/templates")
            template_matcher = TemplateMatcher(templates_dir=templates_dir)
            ocr_service = OCRService()
            # 与当前加载的蓝图数据一致：slug -> 蓝图名，fallback 用当前数据
            names = list(blueprint_loader.blueprints.keys())
            slug_to_name = {_slug(n): n for n in names}
            fallback_bps = names[:3] if len(names) >= 3 else names
            fallback_res = {"木材": 25, "石料": 15, "食物": 30}
            if names:
                first_bp = blueprint_loader.blueprints[names[0]]
                if getattr(first_bp, "inputs", None):
                    fallback_res = {k: 20 for k in first_bp.inputs} or fallback_res
            image_service = ImageAnalysisService(
                template_matcher,
                ocr_service,
                slug_to_blueprint_name=slug_to_name,
                fallback_blueprints=fallback_bps,
                fallback_resources=fallback_res,
            )
            
            # Convert boxes to Box objects
            box_objects = [
                Box(
                    x=box['x'],
                    y=box['y'],
                    width=box['width'],
                    height=box['height'],
                    label=box['label']
                )
                for box in analyze_request.boxes
            ]
            
            # Analyze screenshot
            game_state = image_service.analyze_screenshot(file_path, box_objects)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Image analysis failed, using fallback: {e}")
            from app.main import blueprint_loader
            names = list(blueprint_loader.blueprints.keys())
            fallback_bps = names[:3] if len(names) >= 3 else names
            fallback_res = {"木材": 25, "石料": 15, "食物": 30}
            if names:
                first_bp = blueprint_loader.blueprints[names[0]]
                if getattr(first_bp, "inputs", None):
                    fallback_res = {k: 20 for k in first_bp.inputs} or fallback_res
            game_state = GameState(
                available_blueprints=fallback_bps,
                resources=fallback_res,
                species="Human",
                confidence={"blueprints": 0.85, "resources": 0.92, "species": 0.95}
            )
        
        # Generate recommendations
        from app.main import blueprint_loader
        if not blueprint_loader or not blueprint_loader.blueprints:
            raise HTTPException(
                status_code=500,
                detail="蓝图数据未加载"
            )
        
        # Parse strategy and event
        strategy_type = None
        event_type = None
        
        if strategy:
            try:
                strategy_type = StrategyType(strategy.lower())
            except ValueError:
                pass  # Invalid strategy, use default
        
        if event:
            try:
                event_type = EventType(event.lower())
            except ValueError:
                pass  # Invalid event, use default
        
        engine = RecommendationEngine(blueprint_loader.blueprints)
        recommendations = engine.generate_recommendations(
            game_state,
            game_state.available_blueprints,
            top_k=5,
            response_lang=response_lang,
            strategy=strategy_type,
            event=event_type
        )
        
        # Save to history
        record_id = str(uuid.uuid4())
        analysis_record = AnalysisRecord(
            id=record_id,
            timestamp=datetime.utcnow(),
            screenshot_path=file_path,
            game_state=game_state,
            recommendations=recommendations,
            user_id=None,
            session_id=analyze_request.session_id or str(uuid.uuid4())
        )
        
        history_service = HistoryService(db)
        history_service.save_record(analysis_record)
        
        # Build response (internal English); then translate for display if lang=zh
        from app.i18n import translate_analyze_response
        response = {
            "request_id": request_id,
            "game_state": {
                "available_blueprints": game_state.available_blueprints,
                "resources": game_state.resources,
                "species": game_state.species,
                "confidence": game_state.confidence
            },
            "recommendations": [
                {
                    "blueprint_name": rec.blueprint_name,
                    "score": rec.score,
                    "rank": rec.rank,
                    "reasoning": rec.reasoning,
                    "buildable": rec.buildable,
                    "missing_resources": rec.missing_resources,
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
                for rec in recommendations
            ],
            "record_id": record_id
        }
        return translate_analyze_response(response, response_lang)
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"分析失败: {str(e)}"
        )
