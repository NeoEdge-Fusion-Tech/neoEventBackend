from pydantic import BaseModel
from typing import List

class ProcessBatchRequest(BaseModel):
    photo_ids: List[str]
    event_id: str
    
class ProcessReferenceRequest(BaseModel):
    email: str
    image_url: str
    user_id: str = None
