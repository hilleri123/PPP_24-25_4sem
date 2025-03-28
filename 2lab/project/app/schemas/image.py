from pydantic import BaseModel
from typing import Literal

class ImageRequest(BaseModel):
    image: str  # base64 строка
    algorithm: Literal["otsu", "bradley"]  # only "otsu" or "bradley"

class ImageResponse(BaseModel):
    binarized_image: str  # base64 строка