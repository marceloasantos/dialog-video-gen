import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

from fastapi.openapi.utils import get_openapi
from src.application.bootstrap import bootstrap
from .schemas import VideoRequest
from src.application.config import MASTER_KEY, PRODUCTION
import io
import time
import logging

app = FastAPI(
    title="Byteme API",
    version="0.1.0",
    description="API for generating videos with character voices and subtitles.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Custom exception handler for Pydantic validation errors."""
    missing_fields = [
        str(error["loc"][-1])
        for error in exc.errors()
        if error["type"] == "value_error.missing"
    ]

    if missing_fields:
        field_str = ", ".join(f"'{field}'" for field in missing_fields)
        message = f"Missing required field(s): {field_str}."
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": message},
        )

    # Fallback for other types of validation errors
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request body. Please check your data."},
    )


logger = logging.getLogger(__name__)

# Enforce HTTPS only in production
# HTTPS redirection is handled by Fly.io; avoid app-level redirects to prevent loops.
# if PRODUCTION:
#     app.add_middleware(HTTPSRedirectMiddleware)
#     logger.info("Production mode detected: HTTPS redirect middleware enabled")

logger.info("Startup config: PRODUCTION=%s", PRODUCTION)

video_use_case = bootstrap()
logger.info("Application bootstrapped and video use case initialized")


# Inject API Key security scheme into OpenAPI so Swagger supports X-API-Key
_def_openapi_applied = False


def custom_openapi():
    global _def_openapi_applied
    # In development, always regenerate the OpenAPI schema to avoid stale caches
    if not PRODUCTION:
        app.openapi_schema = None
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    security_schemes.update(
        {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            }
        }
    )
    components["securitySchemes"] = security_schemes
    openapi_schema["components"] = components
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = openapi_schema
    _def_openapi_applied = True
    logger.info("OpenAPI schema generated with ApiKeyAuth security scheme")
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[assignment]


# Simple per-IP rate limiter for the POST /videos endpoint (MVP)
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 30
_rate_limit_state: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    # Prefer X-Forwarded-For if behind a proxy, else fallback to client host
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request):
    if not PRODUCTION:
        return
    now = time.time()
    ip = _client_ip(request)
    timestamps = _rate_limit_state.get(ip, [])
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
    # prune old timestamps
    timestamps = [t for t in timestamps if t >= cutoff]
    if len(timestamps) >= _RATE_LIMIT_MAX_REQUESTS:
        logger.warning(
            "Rate limit exceeded for ip=%s (window=%ss, max=%s)",
            ip,
            _RATE_LIMIT_WINDOW_SECONDS,
            _RATE_LIMIT_MAX_REQUESTS,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )
    timestamps.append(now)
    _rate_limit_state[ip] = timestamps


def require_master_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if MASTER_KEY and x_api_key != MASTER_KEY:
        logger.warning("Unauthorized request: invalid or missing X-API-Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )


# Build dependencies per environment
_video_post_dependencies = [Depends(require_master_key)]
if PRODUCTION:
    _video_post_dependencies.append(Depends(rate_limit))
    logger.info(
        "Rate limiting enabled for POST /videos (window=%ss, max=%s)",
        _RATE_LIMIT_WINDOW_SECONDS,
        _RATE_LIMIT_MAX_REQUESTS,
    )


@app.get("/")
def read_root():
    return {"message": "Byteme API is running"}


@app.post("/videos", dependencies=_video_post_dependencies, tags=["videos"])
async def create_video(video_request: VideoRequest):
    start_time = time.time()
    try:
        logger.info(
            "Video generation request received: dialogues=%s, characters=%s, has_input_path=%s",
            len(video_request.dialogues),
            len(video_request.characters),
            bool(video_request.input_video_path),
        )
        parsed_dialogues = [
            [line.dict() for line in dialogue] for dialogue in video_request.dialogues
        ]
        parsed_characters = {
            name: char.dict() for name, char in video_request.characters.items()
        }

        successful_videos, failed_videos, video_ids = video_use_case.execute(
            parsed_dialogues,
            parsed_characters,
            input_video_path=video_request.input_video_path,
            crop_alignment=video_request.crop_alignment,
            watermark=video_request.watermark,
            watermark_text=video_request.watermark_text,
        )

        if successful_videos > 0 and video_ids:
            primary_video_id = video_ids[0]
            presigned_url = video_use_case.get_video_presigned_url(primary_video_id)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Video generation completed: id=%s, successful=%s, failed=%s, duration_ms=%s",
                primary_video_id,
                successful_videos,
                failed_videos,
                duration_ms,
            )
            return {
                "status": "completed",
                "video_id": primary_video_id,
                "video_ids": video_ids,
                "download_url": f"/videos/{primary_video_id}",
                "presigned_url": presigned_url,
                "successful_videos": successful_videos,
                "failed_videos": failed_videos,
            }
        else:
            logger.error("Video generation failed: no successful outputs produced")
            raise HTTPException(status_code=500, detail="Video generation failed")

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        if PRODUCTION:
            logger.exception(
                "Unhandled error during video generation (duration_ms=%s)", duration_ms
            )
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            logger.exception(
                "Error during video generation (duration_ms=%s): %s",
                duration_ms,
                str(e),
            )
            raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/videos/{video_id}", dependencies=[Depends(require_master_key)], tags=["videos"]
)
async def get_video(video_id: str):
    try:
        video_bytes = video_use_case.get_video(video_id)
        logger.info("Streaming video: id=%s", video_id)
        return StreamingResponse(io.BytesIO(video_bytes), media_type="video/mp4")
    except FileNotFoundError:
        logger.warning("Video not found: id=%s", video_id)
        raise HTTPException(status_code=404, detail="Video not found")


if __name__ == "__main__":
    uvicorn.run(
        "src.interfaces.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        server_header=False,
        date_header=False,
    )
