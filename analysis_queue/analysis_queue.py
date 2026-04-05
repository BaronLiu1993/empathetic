import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

app = Celery("neuro", broker=RABBITMQ_URL)
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
