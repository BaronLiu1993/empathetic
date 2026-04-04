# Neuro

Brain activity prediction from video, audio, and text using Meta's TRIBE v2 model. Includes an HTML purification pipeline for cleaning scraped web content.

## Prerequisites

- Python 3.12
- FFmpeg (`brew install ffmpeg`)
- HuggingFace account with access to LLaMA 3.2 (`huggingface-cli login`)

## Setup

```bash
make setup
source .venv/bin/activate
```

## Usage

### Brain analysis

```python
from service.brain_analysis import predict_from_video, predict_from_text

# From video
preds, segments = predict_from_video("path/to/video.mp4")

# From text
preds, segments = predict_from_text("The cat sat on the mat.")

print(preds.shape)  # (n_timesteps, ~20k vertices)
```

### Text processing

```python
from service.text_processing import clean_text

clean = clean_text("<html>...</html>")  # raw HTML -> clean plain text
```

## Make targets

| Command | Description |
|---------|-------------|
| `make setup` | Create venv and install all deps |
| `make dev` | Run FastAPI server with hot reload |
| `make test` | Run tests |
| `make build` | Build Docker image |
| `make clean` | Remove venv and caches |

## Project structure

```
neuro/
├── main.py                  # FastAPI app
├── service/
│   ├── brain_analysis.py    # TRIBE v2 inference
│   └── text_processing.py   # HTML purification
├── queue/                   # Analysis queue (WIP)
├── router/                  # API routes (WIP)
├── tribev2/                 # TRIBE v2 (inference-only)
└── tests/
```
