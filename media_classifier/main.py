import uvicorn
from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .schemas import ProcessBatchRequest, ProcessReferenceRequest
from .service import process_and_map_photo, process_reference_image

app = FastAPI(title="Face Recognition & Mapping Service (SQLAlchemy)")

def process_batch(photo_ids: list[str], event_id: str, db: Session):
    try:
        for photo_id in photo_ids:
            process_and_map_photo(photo_id, event_id, db)
    except Exception as e:
        print(f"Batch processing failed: {e}")
    finally:
        db.close()

def process_reference(email: str, image_path: str, db: Session):
    try:
        process_reference_image(email, image_path, db)
    finally:
        db.close()

@app.post(
    "/process-batch", 
    tags=["AI Processing"],
    summary="Process a batch of event photos",
    description="Reads a batch of photos from the shared disk, extracts 512D facial vectors using InsightFace, and executes pgvector similarity queries to map faces to registered attendees."
)
async def process_batch_endpoint(
    request: ProcessBatchRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    background_tasks.add_task(process_batch, request.photo_ids, request.event_id, db)
    return {"status": "batch_processing_started", "photos_queued": len(request.photo_ids)}

@app.post(
    "/process-reference",
    tags=["AI Processing"],
    summary="Generate 512D Vector for Attendee Reference Image",
    description="Extracts the facial embeddings from a user's uploaded selfie and stores it in the BiometricIdentity table for future event matching."
)
async def process_reference_endpoint(
    request: ProcessReferenceRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    background_tasks.add_task(process_reference, request.email, request.image_path, db)
    return {"status": "reference_processing_started"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
