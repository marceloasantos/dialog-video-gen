# Environment Configuration

This document explains the environment variables that can be configured for the video production system.

## Required Environment Variables

### ELEVENLABS_API_KEY
Your ElevenLabs API key for voice generation.
```
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Optional Video Production Settings

### CROP_ALIGNMENT
Controls how the video is cropped to 9:16 aspect ratio.

**Options:**
- "center": Always crops from the center of the video
- "left": Always crops from the left side of the video

Required: must be either "center" or "left" (no default applied)

**Example:**
```
CROP_ALIGNMENT=center
```

### INTRO_JUMPER_MIN_START_TIME
Minimum start time in seconds for video cropping. This ensures video segments are never selected from the first N minutes of the source video.

Required: must be a non-negative integer (no default applied)

**Example:**
```
# Skip first 5 minutes
INTRO_JUMPER_MIN_START_TIME=300

# Skip first 15 minutes  
INTRO_JUMPER_MIN_START_TIME=900
```

## Complete .env Example

Create a `.env` file in the project root with:

```
# ElevenLabs API Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Video Production Settings
CROP_ALIGNMENT=center
INTRO_JUMPER_MIN_START_TIME=600
```

## Validation

The system validates these settings on startup and shows clear error messages if:
- Invalid crop alignment values are provided
- Negative intro jumper times are specified
- Required environment variables are missing

Validation occurs during application startup via `src.infrastructure.services.environment_service.check_environment()`.