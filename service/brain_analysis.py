from pathlib import Path

from tribev2 import TribeModel
from pymongo import AsyncMongoClient

uri = "mongodb://localhost:27017/"
client = AsyncMongoClient(uri)
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = TribeModel.from_pretrained("facebook/tribev2", cache_folder="./cache")
    return _model


def get_mongo_write_client():
    uri = "mongodb://localhost:27017/"
    client = AsyncMongoClient(uri)
    return client


def insert_data_to_db(data):
    pass


def predict_from_video(video_path):
    model = _get_model()
    df = model.get_events_dataframe(video_path=video_path)
    preds, segments = model.predict(events=df)
    return preds, segments


def predict_from_text(text):
    model = _get_model()
    tmp = Path("./cache/input.txt")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text)
    df = model.get_events_dataframe(text_path=str(tmp))
    preds, segments = model.predict(events=df)
    return preds, segments


if __name__ == "__main__":
    preds, segments = predict_from_video("/Users/baronliu/Desktop/project/neuro/service/test/news.mp4")
    print(segments)
    print(preds.shape)
