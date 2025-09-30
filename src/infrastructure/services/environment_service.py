import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, StrictStr, ValidationError

# Detect Fly.io runtime early
_RUNNING_ON_FLY = any(
    os.getenv(var_name) for var_name in ("FLY_APP_NAME", "FLY_REGION", "FLY_MACHINE_ID")
)

# Load .env only when not running on Fly.io
if not _RUNNING_ON_FLY:
    load_dotenv()

# --- Project Root ---
# Assumes this file is in src/infrastructure/services
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

# If provided, overrides the cache directory for storage-backed caching
_cache_dir_env = os.getenv("CACHE_DIR") or ".cache"
CACHE_STORAGE_PATH = os.path.join(PROJECT_ROOT, _cache_dir_env)


class _EnvConfig(BaseModel):
    ELEVENLABS_API_KEY: StrictStr
    INTRO_JUMPER_MIN_START_TIME: int = Field(default=3, ge=0)

    # Default expiry for presigned URLs (must be provided by interfaces)
    PRESIGNED_URL_EXPIRES_IN_SECONDS: int = Field(default=3600, ge=1)

    # API master key (optional for local/dev). When set, interfaces should enforce it.
    MASTER_KEY: StrictStr | None = None

    # Production flag (controls HTTPS redirect, error verbosity, etc.)
    PRODUCTION: bool = False

    # Storage backend toggle: "tigris" or "filesystem"
    STORAGE_BACKEND: StrictStr

    # AWS/Tigris S3 configuration
    AWS_ACCESS_KEY_ID: StrictStr | None = None
    AWS_SECRET_ACCESS_KEY: StrictStr | None = None
    AWS_ENDPOINT_URL_S3: StrictStr | None = None
    AWS_REGION: StrictStr | None = None

    # Buckets for input/output assets
    TIGRIS_INPUT_BUCKET: StrictStr | None = None
    TIGRIS_OUTPUT_BUCKET: StrictStr | None = None

    # Optional local paths when using filesystem backend
    FILESYSTEM_INPUT_PATH: StrictStr | None = None
    FILESYSTEM_OUTPUT_PATH: StrictStr | None = None


# Infer production when not explicitly set: default to True on Fly.io
_prod_env = os.getenv("PRODUCTION")
if _prod_env is None or _prod_env.strip() == "":
    _PRODUCTION_BOOL: bool = True if _RUNNING_ON_FLY else False
else:
    _PRODUCTION_BOOL = _prod_env.strip().lower() in {"1", "true", "yes", "on"}

# --- Environment Variables & Configuration ---
try:
    # Prepare a dictionary of environment variables to pass to the config model.
    # This approach avoids passing `None` for unset variables, allowing Pydantic
    # to apply its default values correctly.
    env_data: dict[str, str | int | bool] = {
        "PRODUCTION": _PRODUCTION_BOOL,
        "STORAGE_BACKEND": os.getenv("STORAGE_BACKEND", "tigris"),
    }

    # Conditionally add variables that might be unset
    if api_key := os.getenv("ELEVENLABS_API_KEY"):
        env_data["ELEVENLABS_API_KEY"] = api_key

    if min_start_time := os.getenv("INTRO_JUMPER_MIN_START_TIME"):
        env_data["INTRO_JUMPER_MIN_START_TIME"] = int(min_start_time)

    if expires_in := os.getenv("PRESIGNED_URL_EXPIRES_IN_SECONDS"):
        env_data["PRESIGNED_URL_EXPIRES_IN_SECONDS"] = int(expires_in)

    # Add other optional variables if they exist
    for env_var in [
        "MASTER_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ENDPOINT_URL_S3",
        "AWS_REGION",
        "TIGRIS_INPUT_BUCKET",
        "TIGRIS_OUTPUT_BUCKET",
        "FILESYSTEM_INPUT_PATH",
        "FILESYSTEM_OUTPUT_PATH",
    ]:
        if value := os.getenv(env_var):
            env_data[env_var] = value

    _model_validate = getattr(_EnvConfig, "model_validate", None)
    if callable(_model_validate):
        _env = _model_validate(env_data)
    else:
        _env = _EnvConfig.model_validate(env_data)
except (ValidationError, TypeError, ValueError) as e:
    # Catch validation, type errors (e.g., int(None)), or value errors
    # to provide a consolidated error message.
    raise ValueError(f"Environment validation error: {e}")

ELEVENLABS_API_KEY = _env.ELEVENLABS_API_KEY
INTRO_JUMPER_MIN_START_TIME = _env.INTRO_JUMPER_MIN_START_TIME

# Presigned URL default expiry
PRESIGNED_URL_EXPIRES_IN_SECONDS = _env.PRESIGNED_URL_EXPIRES_IN_SECONDS

# Storage backend
STORAGE_BACKEND = _env.STORAGE_BACKEND.lower()

# API master key (optional)
MASTER_KEY = _env.MASTER_KEY

# Production flag
PRODUCTION = _env.PRODUCTION

# Expose AWS/Tigris settings for storage adapters
AWS_ACCESS_KEY_ID = _env.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = _env.AWS_SECRET_ACCESS_KEY
AWS_ENDPOINT_URL_S3 = _env.AWS_ENDPOINT_URL_S3
AWS_REGION = _env.AWS_REGION

# Expose S3 bucket names
TIGRIS_INPUT_BUCKET = _env.TIGRIS_INPUT_BUCKET
TIGRIS_OUTPUT_BUCKET = _env.TIGRIS_OUTPUT_BUCKET

# Filesystem storage paths (only when STORAGE_BACKEND=filesystem)
FILESYSTEM_INPUT_PATH = (
    os.path.join(PROJECT_ROOT, _env.FILESYSTEM_INPUT_PATH)
    if _env.FILESYSTEM_INPUT_PATH
    else None
)
FILESYSTEM_OUTPUT_PATH = (
    os.path.join(PROJECT_ROOT, _env.FILESYSTEM_OUTPUT_PATH)
    if _env.FILESYSTEM_OUTPUT_PATH
    else None
)

VOICE_SETTINGS = {
    "stability": 0.6,
    "similarity_boost": 1.0,
    "style": 0.0,
    "use_speaker_boost": True,
}

# --- Initial Setup & Validation ---
os.makedirs(CACHE_STORAGE_PATH, exist_ok=True)
