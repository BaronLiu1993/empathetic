from fastapi import APIRouter, HTTPException
from analysis_queue.analysis_worker import process_brain_analysis

router = APIRouter(
    prefix="/v1/api/analysis",
    tags=["analysis"],
)

@router.post("/process")
async def process_text(html: str, user_id: str):
    try:
        task = process_brain_analysis.delay(html, user_id)
        return {"status": "queued", "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))