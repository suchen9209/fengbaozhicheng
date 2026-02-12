"""
FastAPI application entry point for Stormgate Blueprint Assistant
"""
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import db_manager
from app.models import BlueprintDataLoader

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global instances
blueprint_loader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global blueprint_loader
    
    logger.info("Starting Stormgate Blueprint Assistant API")
    
    try:
        # Initialize database
        db_path = os.getenv("DATABASE_PATH", "./data/stormgate.db")
        db_url = f"sqlite:///{db_path}"
        db_manager.database_url = db_url
        db_manager.initialize()
        logger.info(f"Database initialized: {db_path}")
        
        # Load blueprint data（优先 ATS 数据若存在）
        data_path = os.getenv("BLUEPRINTS_DATA_PATH", "")
        if not data_path:
            ats_path = os.path.join(os.path.dirname(__file__), "data", "blueprints_data_ats.json")
            default_path = os.path.join(os.path.dirname(__file__), "data", "blueprints_data.json")
            data_path = ats_path if os.path.exists(ats_path) else default_path
        blueprint_loader = BlueprintDataLoader(data_path)
        blueprint_loader.load()
        logger.info(f"Loaded {len(blueprint_loader.blueprints)} blueprints from {data_path}")
        
        # Create uploads directory
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        Path(upload_dir).mkdir(exist_ok=True)
        logger.info(f"Upload directory ready: {upload_dir}")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("Shutting down Stormgate Blueprint Assistant API")
    db_manager.close()


# Create FastAPI application
app = FastAPI(
    title="Stormgate Blueprint Assistant API",
    description="AI-powered decision support tool for Stormgate game",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"HTTP error: {exc.status_code} - {exc.detail}",
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "request_id": request_id,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Validation error: {exc.errors()}",
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "request_id": request_id,
            "error": "请求参数错误",
            "detail": exc.errors(),
            "status_code": 400
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "request_id": request_id,
            "error": "服务器内部错误",
            "detail": "请稍后重试",
            "status_code": 500
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Stormgate Blueprint Assistant API", "version": "1.0.0"}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected"
    try:
        session = db_manager.get_session()
        session.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    blueprints_status = "loaded" if blueprint_loader and blueprint_loader.blueprints else "not_loaded"
    blueprints_count = len(blueprint_loader.blueprints) if blueprint_loader else 0

    try:
        from app.services.template_matcher import TemplateMatcher
        tm = TemplateMatcher()
        template_count = tm.get_template_count()
        template_matcher_status = f"loaded_{template_count}" if template_count > 0 else "no_templates"
    except Exception as e:
        template_matcher_status = f"error: {str(e)}"

    try:
        from app.services.ocr_service import OCRService
        ocr = OCRService()
        ocr_status = "available" if ocr.is_available() else "unavailable"
    except Exception as e:
        ocr_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "blueprints": blueprints_status,
            "blueprints_count": blueprints_count,
            "ocr": ocr_status,
            "template_matcher": template_matcher_status,
        }
    }


# Include API routers
from app.api.analyze import router as analyze_router
from app.api.history import router as history_router

app.include_router(analyze_router)
app.include_router(history_router)
