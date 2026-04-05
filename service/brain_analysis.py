import asyncio
import tempfile
from pathlib import Path

from tribev2 import TribeModel
from pymongo import AsyncMongoClient
from dotenv import load_dotenv
from service.file_upload import write_file_to_s3, upload_text_pipeline_files
from service.text_processing import clean_text
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

def predict_from_html(raw_html):
    model = _get_model()
    text = clean_text(raw_html)
    tmpdir = tempfile.mkdtemp()
    tmp = Path(tmpdir) / "input.txt"
    tmp.write_text(text)
    df = model.get_events_dataframe(text_path=str(tmp))
    preds, segments = model.predict(events=df)
    return preds, segments, tmpdir

def predict_from_video(video_path):
    model = _get_model()
    df = model.get_events_dataframe(video_path=video_path)
    preds, segments = model.predict(events=df)
    return preds, segments

async def save_brain_analysis_results(source_name, user_id):
    ext = Path(source_name).suffix.lower()
    tmpdir = None
    if ext in VIDEO_EXTENSIONS:
        preds, segments = predict_from_video(source_name)
        write_file_to_s3(user_id, source_name)
    else:
        preds, segments, tmpdir = predict_from_html(source_name)
        upload_text_pipeline_files(user_id, source_name, tmpdir)
    logging.info("[Brain Analysis] Files uploaded to S3.")
    await insert_data_to_db(preds, segments, source_name, user_id)
    logging.info("[Brain Analysis] Results saved to database.")
    return preds, segments

if __name__ == "__main__":
    preds, segments = asyncio.run(save_brain_analysis_results("/Users/baronliu/Desktop/project/neuro/service/test/news.mp4", "user123"))
    print(preds)
