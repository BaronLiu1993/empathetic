import asyncio
import logging

from analysis_queue.analysis_queue import app
from service.brain_analysis import save_brain_analysis_results

logging.basicConfig(level=logging.INFO)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_brain_analysis(self, source_name, user_id):
    logging.info(f"[Worker] Processing: {source_name} for {user_id}")
    try:
        asyncio.run(save_brain_analysis_results(source_name, user_id))
        logging.info(f"[Worker] Completed: {source_name} for {user_id}")
    except Exception as e:
        logging.error(f"[Worker] Failed: {source_name} for {user_id} - {e}")
        raise self.retry(exc=e)
