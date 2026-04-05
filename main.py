from fastapi import FastAPI
from router.analysis_router import router as analysis_router

app = FastAPI()
app.include_router(analysis_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
