from pydoc import doc
import shutil
import tempfile
from pathlib import Path

from pymongo import AsyncMongoClient
from tribev2.tribev2 import TribeModel
from dotenv import load_dotenv
from service.text_processing import clean_text
import os
import logging
import spacy

load_dotenv()

# MongoDB connection
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
_model = None

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

def extract_proper_noun(text, user_id):
    client = get_mongo_write_client()
    db = client["neuro"]
    collection = db["user_data"]
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    proper_nouns = [token.text for token in doc if token.pos_ == "PROPN"]
    collection.update_one(
        {"_id": user_id}, 
        {"$addToSet": {"proper_nouns": {"$each": proper_nouns}}},
        upsert=True
    )
    
def predict_from_html(raw_html):
    model = _get_model()
    text = clean_text(raw_html)

    tmpdir = tempfile.mkdtemp()
    try:
        tmp = Path(tmpdir) / "input.txt"
        tmp.write_text(text)
        model.cache_folder = tmpdir
        df = model.get_events_dataframe(text_path=str(tmp))
        preds, segments = model.predict(events=df)
        return preds, segments
    finally:
        model.cache_folder = "./cache"
        shutil.rmtree(tmpdir, ignore_errors=True)


async def save_brain_analysis_results(source_name, user_id):
    preds, segments = predict_from_html(source_name)
    logging.info("[Brain Analysis] Predictions generated successfully.")
    await insert_data_to_db(preds, segments, source_name, user_id)
    logging.info("[Brain Analysis] Results saved to database.")
    return preds, segments