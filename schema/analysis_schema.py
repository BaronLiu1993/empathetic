from pydantic import BaseModel, Field
from typing import List, Optional

class AnalysisRequest(BaseModel):
    user_id: str = Field(..., description="The ID of the user making the request")
    html: str = Field(..., description="The HTML content to analyze")