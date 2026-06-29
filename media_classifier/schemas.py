from pydantic import BaseModel
from typing import List, Optional

class PhotoItem(BaseModel):
    id: str
    url: str

class ProcessBatchRequest(BaseModel):
    photos: List[PhotoItem]
    event_id: str
    consented_user_ids: Optional[List[str]] = None
    
class ProcessReferenceRequest(BaseModel):
    email: str
    image_url: str
    user_id: Optional[str] = None
