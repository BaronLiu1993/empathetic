import asyncio
from pathlib import Path

from tribev2 import TribeModel
from pymongo import AsyncMongoClient
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# MongoDB connection
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
_model = None
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

# Get the model instance (singleton pattern)
def _get_model():
    global _model
    if _model is None:
        _model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")
    return _model

# Get the MongoDB client
def get_mongo_write_client():
    uri = mongo_uri
    client = AsyncMongoClient(uri, readPreference="secondary")
    return client

def get_mongo_read_client():
    uri = mongo_uri
    client = AsyncMongoClient(uri, readPreference="secondary")
    return client

async def insert_data_to_db(preds, segments, source_name, user_id):
    client = get_mongo_write_client()
    db = client["neuro"]
    collection = db["predictions"]
    print(preds)
    docs = [
        {
            "user_id": user_id,
            "source": source_name,
            "timepoint": float(segments[i].start),
            "duration": float(segments[i].duration),
            "activations": preds[i].tolist(),
        }
        for i in range(len(segments))
    ]
    result = await collection.insert_many(docs)
    print(result.inserted_ids)
    return result.inserted_ids

def predict_from_text(text):
    model = _get_model()
    tmp = Path("./cache/input.txt")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text)
    df = model.get_events_dataframe(text_path=str(tmp))
    preds, segments = model.predict(events=df)
    return preds, segments

def predict_from_video(video_path):
    model = _get_model()
    df = model.get_events_dataframe(video_path=video_path)
    preds, segments = model.predict(events=df)
    return preds, segments

async def save_brain_analysis_results(source_name, user_id):
    ext = Path(source_name).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        preds, segments = predict_from_video(source_name)
    else:
        preds, segments = predict_from_text(source_name)
    logging.info("[Brain Analysis] Predictions generated successfully.")
    await insert_data_to_db(preds, segments, source_name, user_id)
    logging.info("[Brain Analysis] Results saved to database.")
    return preds, segments

if __name__ == "__main__":
    preds, segments = asyncio.run(save_brain_analysis_results("/Users/baronliu/Desktop/project/neuro/service/test/news.mp4", "user123"))
    print(preds)
