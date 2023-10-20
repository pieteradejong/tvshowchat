from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

router = APIRouter()


class SuccessResponse(BaseModel):
    status: Literal["success"]
    message: str


@router.get("/", response_model=SuccessResponse, status_code=200)
def root():
    return {"status": "success", "message": "This application is a TV Show Q&A engine."}
