# byteme: AI-Powered Dialogue Video Generator

ByteMe is a Python application that automatically generates short, engaging videos from dialogue scripts. It synthesizes audio using Text-to-Speech (TTS), creates styled, word-for-word subtitles, and composes a final video ready for social media.

---

## Features

- **Dialogue-Based Video Creation**: Turns a simple script into a dynamic video.
- **AI Voice Generation**: Uses the ElevenLabs API to generate high-quality, expressive audio for each line of dialogue.
- **Intelligent Caching**: Caches generated audio and subtitle data to minimize API calls and speed up subsequent runs.
- **Karaoke-Style Subtitles**: Generates word-level, styled `.ass` subtitles for a professional, engaging look.
- **Automated Video Composition**: Uses FFmpeg to combine video clips, synthesized audio, and subtitles into a final MP4 file.

---

## Architectural Overview

This project is structured following the principles of **Domain-Driven Design (DDD)** to ensure it is maintainable, testable, and ready for future expansion. The architecture was deliberately chosen to manage the complexity of the "Dialogue-Driven Video Production" domain and to support the long-term vision of the project, which includes AI-powered script generation and a public API.

The codebase is organized into four distinct layers:

1.  **Interfaces Layer (`src/interfaces`)**: The entry point for any interaction with the application.
    -   `api/`: Contains the FastAPI app (`main.py`) exposing endpoints for video generation.
2.  **Application Layer (`src/application`)**: Orchestrates the application's use cases by coordinating the domain and infrastructure layers. It doesn't contain business logic itself but directs the workflow.
3.  **Domain Layer (`src/domain`)**: The heart of the application. It contains the core business logic, rules, and models (Entities, Value Objects, and Domain Services) that are independent of any external technology.
4.  **Infrastructure Layer (`src/infrastructure`)**: Contains all the external-facing components and technical details. This includes API clients (ElevenLabs), wrappers for command-line tools (FFmpeg), configuration management, and any other "plumbing."

This layered approach ensures a clean separation of concerns, making it easy to swap out technical components (like changing the TTS provider) without affecting the core business rules.

---

## Project Structure

```
byteme/
├── src/
│   ├── application/    # Orchestrates use cases
│   ├── domain/         # Core business logic and models
│   ├── infrastructure/ # External tools, APIs, and configurations
│   └── interfaces/     # Entry points (API)
├── audio_cache/        # Cached audio files
├── output_videos/      # Final generated videos
├── pyproject.toml      # Project dependencies managed by Poetry
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management.
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system's PATH.

### Installation

1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd byteme
    ```

2.  **Install dependencies using Poetry:**
    ```sh
    poetry install --no-root
    ```

### Configuration

The application requires API keys and other settings to be configured via environment variables.

1.  **Create a `.env` file** in the root of the project:
    ```sh
    touch .env
    ```

2.  **Add the following variables** to your `.env` file:
    ```env
    # Your ElevenLabs API Key
    ELEVENLABS_API_KEY="your_api_key_here"
    
    # Video Production Settings (Optional)
    CROP_ALIGNMENT=center  # Options: "center", "left" (required, no default applied)
    INTRO_JUMPER_MIN_START_TIME=600  # Non-negative integer (required, no default applied)
    ```

The application uses `python-dotenv` to automatically load these variables at runtime.

**Video Production Settings:**
- `CROP_ALIGNMENT`: Controls how videos are cropped to 9:16 aspect ratio
  - `"center"`: Always crops from the center
  - `"left"`: Always crops from the left side  
- `INTRO_JUMPER_MIN_START_TIME`: Minimum start time in seconds (prevents selecting from intro)

---

## How to Run the Application

Start the API server and use the `/videos` endpoint to generate videos:

```sh
poetry run uvicorn src.interfaces.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- Use `curl.sh` as an example request body for `POST /videos`.
- Generated videos will be saved in the `output_videos/` directory.

---

## Future Vision & Roadmap

The current architecture is designed to support the following long-term goals:

-   **Dynamic Characters**: Expand beyond the current set of voices to include a configurable library of characters (e.g., Rick and Morty), where voices and images are dynamically loaded.
-   **AI-Generated Scripts**: Integrate with generative AI models (like GPT-4) to create dialogue scripts on the fly based on user prompts.
-   **Monetization via API**: Develop a public API that allows users to submit their own dialogues and receive a generated video, potentially as a paid service. 


com base nesse email, faça um brainsorm de topicos para videos virais no tiktok. Extraia varios topicos, adicione também os keypoints que devem conter on roteiro



exemplo de resposta:



Keypoints do Roteiro:



O Mito: "Você ouve falar das '7 Magníficas' (Apple, Google, etc.) e acha que são super fortes, certo?"



A Realidade Chocante: Mostre um gráfico simples: Mercado de Ações dos EUA ➡️ 7 Magníficas ➡️ NVIDIA.



A Estatística Matadora: "Mas 42% da receita da NVIDIA vem de apenas 5 dessas empresas (Microsoft, Amazon, Meta, Google, Tesla) comprando chips de IA."



O Risco: "Essas empresas estão comprando chips para produtos de IA que dão prejuízo. Se elas pararem de comprar, a NVIDIA cai."



A Conclusão: "E se a NVIDIA cai, ela puxa todo o mercado de ações junto. Seu fundo de aposentadoria pode estar em risco por causa disso."



