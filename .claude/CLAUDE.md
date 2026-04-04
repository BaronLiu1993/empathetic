# Neuro Project

## Overview
Brain response prediction service using TRIBE v2 — a deep multimodal brain encoding model that predicts fMRI brain responses to naturalistic stimuli (video, audio, text).

## TRIBE v2 Model

- **Source**: facebook/tribev2 on HuggingFace Hub
- **Architecture**: Combines LLaMA 3.2 (text), V-JEPA2 (video), and Wav2Vec-BERT (audio) into a unified Transformer
- **Output**: Predicted fMRI activity on fsaverage5 cortical surface (~20,484 vertices)
- **Checkpoint size**: ~1 GB, cached locally in `./cache/`
- **Access**: Requires HuggingFace access approval for LLaMA 3.2

## Inference API

```python
from tribev2 import TribeModel

model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")

# Video inference (extracts audio, transcribes speech via WhisperX, extracts visual/audio/text features)
df = model.get_events_dataframe(video_path="path/to/video.mp4")
preds, segments = model.predict(events=df)

# Text inference (converts text to speech via gTTS, then processes as audio)
df = model.get_events_dataframe(text_path="path/to/text.txt")
preds, segments = model.predict(events=df)
```

- `preds` shape: `(n_timesteps, 20484)` — one prediction per second, ~20k cortical vertices
- `segments` — corresponding time segments with associated events
- Video pipeline: extracts audio -> transcribes words (WhisperX) -> extracts features (DINOv2 + V-JEPA2, Wav2Vec-BERT, LLaMA 3.2) -> predicts
- Text pipeline: text -> TTS (gTTS) -> same audio pipeline (video extractor auto-removed when no video events)
- Predictions are offset by 5 seconds to compensate for hemodynamic lag

## Stack
- FastAPI (main.py)
- MongoDB (async via pymongo)
- Google Gemini (text processing / HTML cleaning)
- tribev2 (brain encoding model)
